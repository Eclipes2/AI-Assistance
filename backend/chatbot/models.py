"""
MongoEngine document models.

MongoEngine is a Document-Object Mapper (DOM) that works like an ORM
but targets MongoDB instead of SQL.  Each class that extends `Document`
maps to a MongoDB collection.  `EmbeddedDocument` classes are stored
*inside* the parent document (no separate collection).

Collections created here:
  - conversations  → stores chat sessions + their messages
  - faqs           → stores question/answer pairs used as the knowledge base
"""

from datetime import datetime

from mongoengine import Document, EmbeddedDocument, fields


class Message(EmbeddedDocument):
    """
    A single turn in a conversation (user or assistant).
    Stored as an embedded array inside Conversation, so there
    is no extra DB round-trip to fetch messages.
    """

    role = fields.StringField(required=True, choices=["user", "assistant"])
    content = fields.StringField(required=True)
    timestamp = fields.DateTimeField(default=datetime.utcnow)


class Conversation(Document):
    """
    One chat session identified by a UUID session_id.
    Messages are embedded inside the document.
    """

    session_id = fields.StringField(required=True, unique=True)
    messages = fields.EmbeddedDocumentListField(Message, default=list)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "conversations",
        "indexes": ["session_id", "-updated_at"],
    }


class FAQ(Document):
    """
    A single FAQ entry that forms the chatbot's knowledge base.
    These documents are loaded into ChromaDB as vector embeddings
    so the RAG pipeline can retrieve relevant ones at query time.
    """

    question = fields.StringField(required=True)
    answer = fields.StringField(required=True)
    category = fields.StringField(default="general")
    created_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "faqs",
        "indexes": ["category"],
    }
