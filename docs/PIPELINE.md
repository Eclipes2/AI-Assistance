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
    |
    v
[Embed query]  ─────────────────────────────────────────────────────┐
    |                                                               |
    v                                                               |
[Vector store: score threshold search]                              |
  -> FAQs with similarity >= 0.35 (variable count: 0 to 10)        |
    |                                                               |
    └─────────── combine as context <───────────────────────────────┘
                       |
             if no docs above threshold:
             LLM says "I don't know"
                       |
                       v
             [Prompt = system + context + query]
                       |
                       v
                  [Ollama LLM]
                       |
                       v
                  Generated answer
```

---

## LangChain 1.x — LCEL API

This project uses **LangChain 1.x** which removed the old high-level helpers
(`RetrievalQA`, `create_retrieval_chain`) in favour of **LCEL**
(LangChain Expression Language). Steps are composed with the pipe operator `|`:

```python
chain = prompt | llm | StrOutputParser()
answer = chain.invoke({"context": context, "input": user_message})
```

Retrieval is done explicitly before the chain so we can also return source
documents to the frontend.

---

## Components

### 1. Embedding Model — `all-MiniLM-L6-v2`

**Library:** `sentence-transformers` via `langchain-community`

Converts text into a **384-dimensional vector** capturing semantic meaning.
Similar texts produce similar vectors (high cosine similarity).

We use it to:
- Embed every FAQ (question + answer) when building the index
- Embed the user's query at runtime before searching

Why this model?
- Small (~80 MB) and fast on CPU, no GPU required
- Good semantic quality for English Q&A tasks
- Downloaded automatically on first use and cached in `~/.cache/huggingface`

### 2. Vector Store — ChromaDB

**Library:** `chromadb` + `langchain-chroma`

ChromaDB stores FAQ embeddings and performs **cosine similarity search**
using the **HNSW** (Hierarchical Navigable Small World) algorithm.

Storage layout on disk:

```
backend/chroma_db/
    <uuid>/
        data_level0.bin   <- HNSW graph
        header.bin
        length.bin
        link_lists.bin
    chroma.sqlite3        <- metadata, collection info
```

The index is updated by `python manage.py index_faq`.
Documents are cleared and re-added without deleting the collection UUID, so
the running Django server never loses its reference to the collection.

### 3. Retriever — Similarity Score Threshold

```python
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.35, "k": 10},
)
```

Instead of always returning a fixed top-k, the threshold approach returns
**only FAQs that are genuinely relevant**:

| Situation | Results |
|-----------|---------|
| Question matches one specific FAQ | 1 source |
| Broad question spanning several FAQs | 3-6 sources |
| Off-topic / out-of-scope question | 0 sources → fallback answer |

Tuning `SIMILARITY_THRESHOLD` in `ai_pipeline.py`:
- Raise it (e.g. `0.5`) → stricter, fewer but more precise sources
- Lower it (e.g. `0.2`) → more permissive, more sources but possibly noisy

### 4. Prompt Template

```
System:
  You are a friendly and helpful customer support assistant.
  Use ONLY the following FAQ context to answer the question.
  If the answer is not covered by the context, politely say you
  don't know and suggest the user contact a human agent.

  FAQ Context:
  {context}        <- retrieved FAQ chunks injected here

Human: {input}
```

### 5. LLM — Ollama

**Library:** `langchain-ollama`

Ollama is a local LLM server — it downloads and serves open-source models
on your machine. No API key, no data sent to the cloud.

Change the model by editing `OLLAMA_MODEL` in `ai_pipeline.py`:

```python
OLLAMA_MODEL = 'mistral'          # 4 GB, great balance
# OLLAMA_MODEL = 'llama3.2'       # 2 GB, lighter
# OLLAMA_MODEL = 'qwen2.5:14b'    # 9 GB, higher quality
```

---

## Data Flow (Sequence)

```
1. Admin: python manage.py seed_faq
   -> Inserts 18 sample FAQs into MongoDB 'faqs' collection

2. Admin: python manage.py index_faq
   -> Loads all FAQs from MongoDB
   -> For each FAQ: embeds (question + answer) -> 384-dim vector
   -> Clears old documents, adds fresh ones to ChromaDB

3. User types in the Vue.js UI
   -> Autocomplete filters FAQ questions matching the input
   -> User selects suggestion or types freely

4. User sends a message
   -> POST /api/chat/ { message, session_id }

5. Django ChatView
   -> Validates input (session_id accepts null for new sessions)
   -> Calls run_pipeline(user_message)

6. RAG pipeline (ai_pipeline.py)
   a. Embed user_message -> query vector (384 dims)
   b. ChromaDB: return FAQs with cosine_similarity >= 0.35 (max 10)
   c. Format context = concatenate retrieved FAQ page_content
   d. chain = prompt | ChatOllama | StrOutputParser()
   e. answer = chain.invoke({'context': context, 'input': message})
   f. Return { answer, sources }

7. Django saves both turns to MongoDB
   -> Collection 'conversations', embedded Message subdocuments

8. API returns { answer, sources, session_id }

9. Vue.js
   -> Appends bubbles, auto-scrolls
   -> Renders answer as Markdown (bold, lists, code)
   -> Shows collapsible 'N sources consultees' with category + question
```

---

## Caching Strategy

Module-level singletons are initialised once per Django worker process
and reused for every subsequent request (avoids reloading the model):

```python
_embeddings = None    # HuggingFaceEmbeddings (~80 MB loaded once)
_vector_store = None  # Chroma client
_llm_chain = None     # prompt | ChatOllama | StrOutputParser

def get_llm_chain():
    global _llm_chain
    if _llm_chain is None:
        _llm_chain = prompt | get_llm() | StrOutputParser()
    return _llm_chain
```

After `index_faq` completes, `_vector_store` and `_llm_chain` are reset
to `None` so the next request reloads the updated index.

---

## Possible Improvements

| Improvement | How |
|-------------|-----|
| Streaming responses | Ollama stream endpoint + Django StreamingHttpResponse + EventSource on frontend |
| Conversation memory | Append last N message pairs to the prompt |
| MMR retrieval | `search_type='mmr'` to reduce redundant sources |
| Hybrid search | Combine vector similarity with BM25 keyword search |
| Re-ranking | Use a cross-encoder to re-score retrieved documents |
| Evaluation | RAGAS framework to measure faithfulness and relevance |
| Authentication | JWT auth to protect the /api/chat/ endpoint |
