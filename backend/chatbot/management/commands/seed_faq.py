"""
Management command: seed_faq
Usage: python manage.py seed_faq

Inserts a realistic set of customer-support FAQ entries into MongoDB.
Running the command twice will NOT create duplicates (idempotent).
"""

from django.core.management.base import BaseCommand

from chatbot.models import FAQ

SAMPLE_FAQS = [
    # ── Account ───────────────────────────────────────────────────────────────
    {
        "question": "How do I reset my password?",
        "answer": (
            "Go to the login page and click 'Forgot Password'. "
            "Enter your email address and we will send you a reset link within 5 minutes. "
            "Check your spam/junk folder if the email doesn't appear in your inbox."
        ),
        "category": "account",
    },
    {
        "question": "How do I update my email address?",
        "answer": (
            "Log in and navigate to Account Settings → Personal Info → Email. "
            "Enter your new address and confirm with your current password. "
            "A verification link will be sent to the new address."
        ),
        "category": "account",
    },
    {
        "question": "How do I add team members?",
        "answer": (
            "From your Dashboard, go to Team Management → Invite Members. "
            "Enter email addresses and select a role (Admin, Editor, or Viewer). "
            "Each person will receive an invitation email valid for 48 hours."
        ),
        "category": "account",
    },
    {
        "question": "Can I export my data?",
        "answer": (
            "Yes. Go to Settings → Privacy → Export Data and click 'Request Export'. "
            "You will receive a download link by email within 2 hours. "
            "The archive includes all your data in JSON and CSV formats."
        ),
        "category": "account",
    },
    {
        "question": "How do I delete my account?",
        "answer": (
            "Go to Settings → Account → Delete Account. "
            "You will be asked to confirm with your password. "
            "Account deletion is permanent and all associated data will be removed after 30 days."
        ),
        "category": "account",
    },
    # ── Billing ───────────────────────────────────────────────────────────────
    {
        "question": "How do I cancel my subscription?",
        "answer": (
            "Go to Account Settings → Subscription → Cancel Plan. "
            "Your access continues until the end of the current billing period. "
            "You won't be charged after cancellation."
        ),
        "category": "billing",
    },
    {
        "question": "What payment methods do you accept?",
        "answer": (
            "We accept all major credit and debit cards (Visa, Mastercard, American Express), "
            "PayPal, and bank transfers for annual plans. "
            "All payments are processed securely through Stripe."
        ),
        "category": "billing",
    },
    {
        "question": "How do I upgrade my plan?",
        "answer": (
            "Go to Account Settings → Subscription → Upgrade Plan. "
            "Select your desired tier and confirm. "
            "The upgrade takes effect immediately and billing is prorated for the remainder of the billing period."
        ),
        "category": "billing",
    },
    {
        "question": "What is your refund policy?",
        "answer": (
            "We offer a 30-day money-back guarantee for all new subscriptions. "
            "Contact support@example.com with your order ID to request a refund. "
            "Refunds are processed within 5–10 business days."
        ),
        "category": "billing",
    },
    {
        "question": "Why was I charged twice?",
        "answer": (
            "A double charge usually occurs when a payment is retried after a temporary failure. "
            "Please contact support@example.com with your billing email and we will investigate "
            "and issue a refund for the duplicate charge within 3 business days."
        ),
        "category": "billing",
    },
    # ── Support ───────────────────────────────────────────────────────────────
    {
        "question": "How do I contact customer support?",
        "answer": (
            "You can reach our team via: "
            "Email: support@example.com (response within 24 hours), "
            "Live chat: available Monday–Friday, 9 am – 6 pm CET, "
            "Phone: +1-800-EXAMPLE (business hours only)."
        ),
        "category": "support",
    },
    {
        "question": "How long does it take to get a support response?",
        "answer": (
            "Email responses are sent within 24 hours on business days. "
            "Live chat typically connects you with an agent in under 5 minutes. "
            "Critical issues (service outages) are addressed within 2 hours around the clock."
        ),
        "category": "support",
    },
    # ── Security ──────────────────────────────────────────────────────────────
    {
        "question": "Is my data secure?",
        "answer": (
            "Yes. We use AES-256 encryption for data at rest and TLS 1.3 for data in transit. "
            "We are GDPR and SOC 2 Type II compliant. "
            "Our infrastructure is hosted on ISO 27001-certified data centres."
        ),
        "category": "security",
    },
    {
        "question": "Do you share my data with third parties?",
        "answer": (
            "We never sell your personal data. "
            "We only share data with trusted sub-processors (e.g. payment provider, analytics) "
            "as described in our Privacy Policy. You can request a full list of sub-processors at any time."
        ),
        "category": "security",
    },
    {
        "question": "How do I enable two-factor authentication?",
        "answer": (
            "Go to Account Settings → Security → Two-Factor Authentication and click 'Enable'. "
            "Scan the QR code with an authenticator app (e.g. Google Authenticator, Authy) "
            "and enter the 6-digit code to confirm setup."
        ),
        "category": "security",
    },
    # ── Technical ─────────────────────────────────────────────────────────────
    {
        "question": "What browsers are supported?",
        "answer": (
            "Our platform supports the latest two major versions of Chrome, Firefox, Safari, and Edge. "
            "We recommend keeping your browser up to date for the best experience and security."
        ),
        "category": "technical",
    },
    {
        "question": "The application is slow — what can I do?",
        "answer": (
            "Try clearing your browser cache (Ctrl+Shift+Del) and disabling browser extensions. "
            "Check your internet connection speed. "
            "If the issue persists, contact support with your browser version and a screenshot of the slow page."
        ),
        "category": "technical",
    },
    {
        "question": "Is there a mobile app available?",
        "answer": (
            "Yes! Our mobile app is available for iOS (App Store) and Android (Google Play). "
            "Search for 'ExampleApp' in your store. "
            "The app supports all core features including chat, file upload, and notifications."
        ),
        "category": "technical",
    },
]


class Command(BaseCommand):
    help = "Seed the MongoDB FAQ collection with sample data (idempotent)."

    def handle(self, *args, **options):
        inserted = 0
        skipped = 0

        for data in SAMPLE_FAQS:
            exists = FAQ.objects(question=data["question"]).first()
            if exists:
                skipped += 1
                continue
            FAQ(**data).save()
            inserted += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — {inserted} FAQ(s) inserted, {skipped} already present."
            )
        )
