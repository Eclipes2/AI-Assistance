# AI Customer Support Chatbot

A full-stack, locally-runnable AI chatbot for customer support — built as a self-learning project.

**Stack:** Vue.js 3 · Django REST Framework · LangChain · Ollama (Mistral 7B) · ChromaDB · MongoDB

---

## Architecture

```
┌─────────────────┐     REST API      ┌──────────────────────┐
│  Vue.js 3 (Vite)│ ◄────────────── ► │  Django + DRF        │
│ Pinia · Tailwind│                   │  Python 3.11         │
└─────────────────┘                   └──────────┬───────────┘
                                                 │
                           ┌─────────────────────┼──────────────────┐
                           ▼                     ▼                  ▼
                     ┌──────────┐        ┌──────────────┐   ┌──────────────┐
                     │ MongoDB  │        │  ChromaDB    │   │  Ollama      │
                     │ (history │        │ (vector store│   │  Mistral 7B  │
                     │  + FAQs) │        │  embeddings) │   │  (local LLM) │
                     └──────────┘        └──────────────┘   └──────────────┘
```

See [docs/PIPELINE.md](docs/PIPELINE.md) for a deep dive into the RAG pipeline.

---

## Prerequisites

| Tool | Install |
|------|---------|
| Docker Desktop | https://www.docker.com/products/docker-desktop/ |
| Python 3.11+ | https://www.python.org/downloads/ |
| Node.js 20+ | https://nodejs.org/ |
| Ollama | https://ollama.com/ |

After installing Ollama, pull the model:

```bash
ollama pull mistral
```

---

## Quick Start (Development)

### 1 — Start MongoDB

```bash
docker compose up mongodb -d
```

### 2 — Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies (~500 MB including PyTorch for sentence-transformers)
pip install -r requirements.txt

# Copy environment file and adjust if needed
cp .env.example .env   # Windows: copy .env.example .env

# Create SQLite tables used by Django auth/contenttypes (one-time)
python manage.py migrate

# Seed the FAQ knowledge base into MongoDB
python manage.py seed_faq

# Index FAQs into ChromaDB (downloads embedding model on first run ~80 MB)
python manage.py index_faq

# Start the API server
python manage.py runserver
```

The API is now available at http://localhost:8000

### 3 — Frontend

```bash
cd frontend

npm install
npm run dev
```

Open http://localhost:5173 in your browser.

### 4 — Make sure Ollama is running

```bash
# In a separate terminal
ollama serve
# (or just open the Ollama desktop app)
```

---

## Full Docker Compose (All Services)

```bash
docker compose up --build
```

> **Note:** Ollama runs on your host machine. The backend container reaches it
> via `host.docker.internal:11434`. On Linux you may need to add
> `--add-host host.docker.internal:host-gateway` to the backend service in
> `docker-compose.yml`.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health/` | Service health check |
| `POST` | `/api/chat/` | Send a message, get AI reply |
| `GET` | `/api/conversations/` | List recent conversations |
| `GET` | `/api/conversations/{session_id}/` | Full history for one session |
| `GET` | `/api/faq/` | List all FAQ entries |
| `POST` | `/api/faq/` | Create a new FAQ entry |

### Example: Chat request

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I reset my password?"}'
```

Response:

```json
{
  "answer": "To reset your password, click 'Forgot Password' on the login page...",
  "sources": [
    { "question": "How do I reset my password?", "category": "account" }
  ],
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Management Commands

```bash
# Seed FAQ data into MongoDB (idempotent)
python manage.py seed_faq

# Index all FAQs from MongoDB into ChromaDB
python manage.py index_faq
```

Run `index_faq` after every time you add or update FAQ entries.

---

## Project Structure

```
AI-Assistance/
├── backend/
│   ├── config/               # Django project settings
│   │   ├── settings.py
│   │   └── urls.py
│   ├── chatbot/              # Main Django app
│   │   ├── models.py         # MongoEngine documents
│   │   ├── views.py          # DRF API views
│   │   ├── serializers.py    # Input validation + output helpers
│   │   ├── urls.py           # URL routing
│   │   ├── ai_pipeline.py    # RAG chain (LangChain + Ollama + ChromaDB)
│   │   └── management/
│   │       └── commands/
│   │           ├── seed_faq.py   # Populate MongoDB with sample FAQs
│   │           └── index_faq.py  # Build ChromaDB vector index
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.vue    # Main chat UI
│   │   │   ├── MessageBubble.vue # Single message display
│   │   │   └── FAQPanel.vue      # Sidebar with FAQ catalogue
│   │   ├── stores/
│   │   │   └── chat.js           # Pinia state store
│   │   └── views/
│   │       └── HomeView.vue      # Page layout
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml
└── docs/
    └── PIPELINE.md           # AI design document
```

---

## Learning Notes

| Phase | What you learn |
|-------|---------------|
| Backend setup | Django project layout, virtual environments, DRF |
| MongoEngine | Document-based ODM vs SQL ORM, embedded documents |
| AI pipeline | RAG architecture, embeddings, vector similarity search |
| LangChain | Chain abstraction, prompt templates, retrievers |
| Ollama | Running LLMs locally, model serving |
| Vue 3 | Composition API, `<script setup>`, reactive refs |
| Pinia | State stores, actions, getters |
| Tailwind CSS | Utility-first styling, responsive layout |
| Docker Compose | Multi-service orchestration, networking |
