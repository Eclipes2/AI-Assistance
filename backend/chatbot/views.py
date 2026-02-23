"""
API Views — each class handles one or more HTTP methods for an endpoint.

Endpoints:
  GET  /api/health/                      → health check (DB + AI service status)
  POST /api/chat/                        → send a message, receive AI reply
  GET  /api/conversations/               → list recent conversations
  GET  /api/conversations/<session_id>/  → full history for one session
  GET  /api/faq/                         → list all FAQ entries
  POST /api/faq/                         → create a new FAQ entry
"""

import uuid
from datetime import datetime

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai_pipeline import run_pipeline
from .models import FAQ, Conversation, Message
from .serializers import (
    ChatInputSerializer,
    FAQInputSerializer,
    serialize_conversation_detail,
    serialize_conversation_summary,
    serialize_faq,
)


class ChatView(APIView):
    """
    POST /api/chat/
    Body: { "message": "...", "session_id": "..." (optional) }

    Flow:
      1. Validate input
      2. Find or create a Conversation document
      3. Append the user message
      4. Run the RAG pipeline to get an AI answer
      5. Append the assistant message
      6. Persist and return the answer
    """

    def post(self, request):
        serializer = ChatInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data["message"]
        session_id = serializer.validated_data.get("session_id") or str(uuid.uuid4())

        # Get or create the conversation document
        conversation = Conversation.objects(session_id=session_id).first()
        if not conversation:
            conversation = Conversation(session_id=session_id)

        # Persist the user turn immediately
        conversation.messages.append(
            Message(role="user", content=user_message)
        )

        # Run the AI pipeline (RAG)
        try:
            result = run_pipeline(user_message)
            answer = result["answer"]
            sources = result["sources"]
        except Exception as exc:
            return Response(
                {"error": f"AI pipeline error: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Persist the assistant turn
        conversation.messages.append(
            Message(role="assistant", content=answer)
        )
        conversation.updated_at = datetime.utcnow()
        conversation.save()

        return Response(
            {
                "answer": answer,
                "sources": sources,
                "session_id": session_id,
            }
        )


class ConversationListView(APIView):
    """GET /api/conversations/ — returns the 20 most recently active sessions."""

    def get(self, request):
        conversations = (
            Conversation.objects().order_by("-updated_at").limit(20)
        )
        return Response([serialize_conversation_summary(c) for c in conversations])


class ConversationDetailView(APIView):
    """GET /api/conversations/<session_id>/ — full message history."""

    def get(self, request, session_id):
        conversation = Conversation.objects(session_id=session_id).first()
        if not conversation:
            return Response(
                {"error": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(serialize_conversation_detail(conversation))


class HealthView(APIView):
    """GET /api/health/ — returns service status for Docker health checks."""

    def get(self, request):
        # Ping MongoDB
        try:
            FAQ.objects().limit(1).first()
            mongo_ok = True
        except Exception:
            mongo_ok = False

        all_ok = mongo_ok
        return Response(
            {
                "status": "ok" if all_ok else "degraded",
                "mongodb": "ok" if mongo_ok else "error",
            },
            status=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class FAQView(APIView):
    """
    GET  /api/faq/ → list all FAQs (optionally filtered by ?category=)
    POST /api/faq/ → create a new FAQ entry
    """

    def get(self, request):
        category = request.query_params.get("category")
        qs = FAQ.objects(category=category) if category else FAQ.objects()
        faqs = qs.order_by("category", "question")
        return Response([serialize_faq(f) for f in faqs])

    def post(self, request):
        serializer = FAQInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        faq = FAQ(**serializer.validated_data)
        faq.save()
        return Response(serialize_faq(faq), status=status.HTTP_201_CREATED)
