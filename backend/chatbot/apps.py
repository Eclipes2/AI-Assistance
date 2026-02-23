import os

from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chatbot"

    def ready(self):
        """Connect MongoEngine to MongoDB when Django starts."""
        import mongoengine

        mongodb_uri = os.environ.get(
            "MONGODB_URI", "mongodb://localhost:27017/chatbot_db"
        )
        mongoengine.connect(host=mongodb_uri)
