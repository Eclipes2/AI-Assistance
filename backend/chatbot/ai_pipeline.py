"""
RAG (Retrieval-Augmented Generation) pipeline — LangChain 1.x LCEL API.

LangChain 1.x removed the high-level chain helpers (RetrievalQA,
create_retrieval_chain) in favour of LCEL — the LangChain Expression Language.
LCEL lets you compose pipeline steps with the pipe operator `|`:

    retriever | format_docs | prompt | llm | output_parser

How the pipeline works:
  1. FAQ documents are indexed into ChromaDB as vector embeddings.
  2. For each user message:
       a. Retrieve top-3 similar FAQ documents from ChromaDB.
       b. Format them as plain text context.
       c. Build a prompt: system instructions + FAQ context + user question.
       d. Send to Ollama (local LLM).
       e. Parse the streamed response into a string.

Key concepts:
  - Embeddings  : text → dense vector (384-dim) capturing semantic meaning.
  - Vector store: DB optimised for cosine-similarity search over vectors.
  - Retriever   : wraps the vector store to return top-k similar documents.
  - LCEL chain  : steps connected with | — each step's output feeds the next.
"""

from pathlib import Path

from django.conf import settings
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama

# ── Config ─────────────────────────────────────────────────────────────────────

CHROMA_PERSIST_DIR = str(Path(__file__).resolve().parent.parent / "chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # ~80 MB, fast on CPU, 384-dim vectors
OLLAMA_MODEL = "gpt-oss:120b-cloud"

# Dynamic retrieval: return every FAQ whose similarity score is above this
# threshold (0.0–1.0). Lower = more permissive, higher = stricter.
# SIMILARITY_THRESHOLD = 0.35 means "at least 35% semantically similar".
# MAX_DOCS caps the retrieval to avoid bloating the LLM prompt.
SIMILARITY_THRESHOLD = 0.35
MAX_DOCS = 10

SYSTEM_PROMPT = (
    "You are a friendly and helpful customer support assistant. "
    "Use ONLY the following FAQ context to answer the question. "
    "If the answer is not covered by the context, politely say you don't know "
    "and suggest the user contact a human agent.\n\n"
    "FAQ Context:\n{context}"
)

# ── Module-level singletons ────────────────────────────────────────────────────

_embeddings = None
_vector_store = None
_llm_chain = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def get_vector_store() -> Chroma:
    global _vector_store
    if _vector_store is None:
        _vector_store = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=get_embeddings(),
            collection_name="faqs",
        )
    return _vector_store


def get_llm() -> ChatOllama:
    ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    return ChatOllama(base_url=ollama_url, model=OLLAMA_MODEL, temperature=0.2)


def get_llm_chain():
    """
    Build and cache the prompt → LLM → parser chain.

    This part is stateless (no retrieval) and can be safely cached.
    Retrieval is done separately so we can also return source documents.
    """
    global _llm_chain
    if _llm_chain is None:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "{input}"),
            ]
        )
        _llm_chain = prompt | get_llm() | StrOutputParser()
    return _llm_chain


# ── Public API ────────────────────────────────────────────────────────────────

def run_pipeline(user_message: str) -> dict:
    """
    Full RAG pipeline:
      1. Retrieve the top-k most relevant FAQ documents.
      2. Format them as a context string.
      3. Run prompt | llm | parser to get the answer.

    Returns:
        {"answer": str, "sources": [{"question": str, "category": str}]}
    """
    # Step 1 — retrieve: only documents above the similarity threshold.
    # search_type="similarity_score_threshold" returns a variable number of
    # results depending on relevance — could be 1 or many.
    retriever = get_vector_store().as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "score_threshold": SIMILARITY_THRESHOLD,
            "k": MAX_DOCS,
        },
    )
    docs = retriever.invoke(user_message)

    # Step 2 — format context
    context = "\n\n".join(doc.page_content for doc in docs)

    # Step 3 — generate answer
    chain = get_llm_chain()
    answer = chain.invoke({"context": context, "input": user_message})

    sources = [
        {
            "question": doc.metadata.get("question", ""),
            "category": doc.metadata.get("category", ""),
        }
        for doc in docs
    ]

    return {"answer": answer.strip(), "sources": sources}


def index_faqs_to_chroma(faqs: list) -> int:
    """
    Index a list of FAQ dicts into ChromaDB.
    Each dict needs: id, question, answer, category.
    Wipes the collection first to avoid duplicates.
    Returns the number of indexed documents.
    """
    if not faqs:
        return 0

    from langchain_core.documents import Document as LCDocument

    documents = [
        LCDocument(
            page_content=f"Q: {faq['question']}\nA: {faq['answer']}",
            metadata={
                "faq_id": faq["id"],
                "question": faq["question"],
                "category": faq["category"],
            },
        )
        for faq in faqs
    ]

    # Get or create the collection, then replace all its documents.
    # We avoid delete_collection() because the running Django process
    # may have a cached reference to the old collection UUID.
    store = Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=get_embeddings(),
        collection_name="faqs",
    )

    # Remove all existing documents (keeps the collection UUID stable)
    existing_ids = store.get()["ids"]
    if existing_ids:
        store.delete(ids=existing_ids)

    # Add the fresh documents
    store.add_documents(documents)

    # Invalidate singletons so the next request picks up the updated store
    global _vector_store, _llm_chain
    _vector_store = None
    _llm_chain = None

    return len(documents)
