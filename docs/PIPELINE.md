# AI Pipeline Design — RAG Architecture

This document explains the Retrieval-Augmented Generation (RAG) pipeline
powering the chatbot.

---

## What is RAG?

A plain LLM (Large Language Model) only knows what it was trained on.
If you ask it about your company's specific refund policy, it has no idea.

**RAG** solves this by:
1. Storing your domain knowledge (FAQs, docs) in a **vector database**
2. At query time, **retrieving** the most relevant snippets
3. **Injecting** those snippets into the LLM prompt as context

The LLM then generates an answer that is *grounded* in your actual data.

```
User query
    │
    ▼
[Embed query]  ──────────────────────────────────────────────────┐
    │                                                            │
    ▼                                                            │
[Vector store: similarity search]  → top-3 FAQ chunks            │
    │                                                            │
    └──────────── combine as context ◄───────────────────────────┘
                        │
                        ▼
              [Prompt = system + context + query]
                        │
                        ▼
                   [Ollama LLM]
                        │
                        ▼
                   Generated answer
```

---

## LangChain Version Note

This project uses **LangChain 1.x** which introduced LCEL
(LangChain Expression Language). The older high-level helpers
(`RetrievalQA`, `create_retrieval_chain`) were removed. The pipeline
is built manually using LCEL pipe operators:

```python
chain = prompt | llm | StrOutputParser()
answer = chain.invoke({"context": context, "input": user_message})
```

Retrieval is done separately so we can also capture source documents
for display in the UI.

---

## Components

### 1. Embedding Model — `all-MiniLM-L6-v2`

**Library:** `sentence-transformers` via `langchain-community`

This model converts a piece of text into a **384-dimensional vector**
(a list of 384 floats). Texts that are semantically similar will have
vectors that are close together in that 384-dimensional space.

We use it to:
- Embed every FAQ (question + answer) when building the index
- Embed the user's query at runtime before searching

Why this model?
- Very small (~80 MB) and fast on CPU
- Good semantic quality for English Q&A tasks
- No GPU required

### 2. Vector Store — ChromaDB

**Library:** `chromadb` + `langchain-chroma`

ChromaDB stores the FAQ embeddings and performs **cosine similarity
search** to find which FAQs are most relevant to the user's query.

Storage layout on disk:

```
backend/chroma_db/       ← persisted ChromaDB data
    faqs/                ← collection name
        *.bin            ← HNSW index files
        *.pkl            ← embedding vectors
```

The index is rebuilt from scratch by `python manage.py index_faq`.

### 3. Retriever

Configured to return the **top 3** most similar FAQ documents (`k=3`).
This number is a trade-off:
- Too few → risk missing relevant context
- Too many → bloats the prompt, confuses the LLM, increases latency

### 4. Prompt Template

```
You are a friendly and helpful customer support assistant.
Use ONLY the following FAQ context to answer the question.
If the answer is not covered by the context, politely say you don't know
and suggest the user contact a human agent.

FAQ Context:
{context}          ← top-3 retrieved FAQ snippets injected here

User Question: {question}

Answer:
```

The `{context}` and `{question}` placeholders are filled by LangChain's
`RetrievalQA` chain.

### 5. LLM — Ollama (Mistral 7B)

**Library:** `langchain-ollama`

Ollama is a local LLM server. It downloads and serves open-source models
on your machine. No API key, no data sent to the cloud.

`mistral` (7B parameters) is a good balance of:
- Response quality
- Speed (runs well on modern CPUs, fast on GPU)
- Memory usage (~5 GB RAM)

Alternatively you can use `llama3.2`, `qwen2.5`, or any model available
at https://ollama.com/library.

To switch model, change `OLLAMA_MODEL` in `ai_pipeline.py`.

---

## Data Flow (Sequence)

```
1. Admin runs: python manage.py seed_faq
   └─ Inserts 18 sample FAQs into MongoDB collection "faqs"

2. Admin runs: python manage.py index_faq
   └─ Loads all FAQs from MongoDB
   └─ For each FAQ: embeds (question + answer) → 384-dim vector
   └─ Stores vectors + metadata in ChromaDB ("faqs" collection)

3. User sends a message via the Vue.js UI
   └─ POST /api/chat/ { message, session_id }

4. Django ChatView receives the request
   └─ Validates input
   └─ Calls run_pipeline(user_message)

5. RAG pipeline (ai_pipeline.py)
   a. Embed user_message → query vector (384 dims)
   b. ChromaDB: cosine similarity(query_vector, all_faq_vectors) → top 3
   c. Build prompt: system_prompt + retrieved_faqs + user_message
   d. Send prompt to Ollama Mistral → streamed text response
   e. Return { answer, sources }

6. Django saves both turns (user + assistant) to MongoDB
   └─ Collection "conversations", embedded Message subdocuments

7. API returns { answer, sources, session_id } to the frontend
8. Vue.js appends the message to the chat list and scrolls down
```

---

## Caching Strategy

The embedding model, vector store, and RAG chain are all module-level
singletons (initialised once, reused for every request):

```python
_embeddings = None
_vector_store = None
_rag_chain = None

def get_rag_chain():
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = build_rag_chain()   # expensive — done once
    return _rag_chain
```

When `index_faq` is run, these singletons are reset to `None` so the
next request picks up the freshly indexed data.

---

## Possible Improvements

| Improvement | How |
|-------------|-----|
| Streaming responses | Use Ollama's `/api/chat` stream endpoint + Django `StreamingHttpResponse` + SSE on the frontend |
| Better retrieval | Use `MMR` (Maximal Marginal Relevance) instead of pure similarity to reduce redundant results |
| Conversation memory | Pass the last N turns as additional context in the prompt |
| Hybrid search | Combine vector similarity with BM25 keyword search |
| Larger model | Switch `OLLAMA_MODEL` to `llama3.1:8b` or `mistral-nemo` for better quality |
| Evaluation | Use RAGAS framework to measure answer faithfulness and relevance |
| Authentication | Add JWT auth to protect the chat endpoint |
