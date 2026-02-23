from django.urls import path

from .views import (
    ChatView,
    ConversationDetailView,
    ConversationListView,
    FAQView,
    HealthView,
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("chat/", ChatView.as_view(), name="chat"),
    path("conversations/", ConversationListView.as_view(), name="conversations"),
    path(
        "conversations/<str:session_id>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path("faq/", FAQView.as_view(), name="faq"),
]
