"""
Management command: index_faq
Usage: python manage.py index_faq

Loads all FAQ documents from MongoDB, generates sentence-transformer
embeddings, and stores them in ChromaDB for vector similarity search.

Run this command:
  - After seeding the database for the first time (python manage.py seed_faq)
  - Whenever you add/update FAQ entries
"""

from django.core.management.base import BaseCommand

from chatbot.ai_pipeline import index_faqs_to_chroma
from chatbot.models import FAQ


class Command(BaseCommand):
    help = "Index all FAQ documents from MongoDB into ChromaDB (vector store)."

    def handle(self, *args, **options):
        self.stdout.write("Loading FAQs from MongoDB…")

        faqs = FAQ.objects()
        faq_list = [
            {
                "id": str(f.id),
                "question": f.question,
                "answer": f.answer,
                "category": f.category,
            }
            for f in faqs
        ]

        if not faq_list:
            self.stdout.write(
                self.style.WARNING(
                    "No FAQs found in MongoDB. "
                    "Run 'python manage.py seed_faq' first."
                )
            )
            return

        self.stdout.write(
            f"Found {len(faq_list)} FAQ(s). Generating embeddings and indexing…"
        )
        self.stdout.write(
            "  (first run downloads the all-MiniLM-L6-v2 model — this may take a minute)"
        )

        count = index_faqs_to_chroma(faq_list)

        self.stdout.write(
            self.style.SUCCESS(f"Done — {count} document(s) indexed into ChromaDB.")
        )
