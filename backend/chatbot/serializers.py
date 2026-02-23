"""
Serializers convert MongoEngine documents to/from Python dicts.

We cannot use DRF ModelSerializer because that is designed for
Django ORM models.  Instead we use plain Serializer classes for
*input validation* and simple helper functions for *output formatting*.
"""

from rest_framework import serializers


# ── Input validators ──────────────────────────────────────────────────────────

class ChatInputSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
    session_id = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)


class FAQInputSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500)
    answer = serializers.CharField(max_length=2000)
    category = serializers.CharField(max_length=100, default="general")


# ── Output helpers ────────────────────────────────────────────────────────────

def serialize_message(msg):
    return {
        "role": msg.role,
        "content": msg.content,
        "timestamp": msg.timestamp.isoformat(),
    }


def serialize_conversation_summary(conv):
    preview = conv.messages[0].content[:120] if conv.messages else ""
    return {
        "session_id": conv.session_id,
        "message_count": len(conv.messages),
        "preview": preview,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
    }


def serialize_conversation_detail(conv):
    return {
        "session_id": conv.session_id,
        "messages": [serialize_message(m) for m in conv.messages],
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
    }


def serialize_faq(faq):
    return {
        "id": str(faq.id),
        "question": faq.question,
        "answer": faq.answer,
        "category": faq.category,
        "created_at": faq.created_at.isoformat(),
    }
