---
name: AI Chatbot Full-Stack
overview: Build a local AI customer support chatbot from scratch using Vue.js 3 (frontend), Django REST API (backend), Ollama for the local LLM, and MongoDB for persistence — structured as a self-learning project with clear phases.
todos:
  - id: phase1-scaffold
    content: "Phase 1: Project scaffolding — repo structure, docker-compose.yml (MongoDB), .gitignore, Django init, Vue 3 + Vite scaffold"
    status: completed
  - id: phase2-backend
    content: "Phase 2: Backend models & API — MongoEngine models (Conversation, Message, FAQ), DRF serializers, views, URL routing"
    status: completed
  - id: phase3-ai
    content: "Phase 3: AI pipeline — LangChain RAG chain, Ollama LLM integration, sentence-transformers embeddings, ChromaDB vector store, FAQ indexing script"
    status: completed
  - id: phase4-frontend
    content: "Phase 4: Frontend chat UI — ChatWindow.vue, MessageBubble.vue, Pinia store, axios API calls, Tailwind styling"
    status: completed
  - id: phase5-integration
    content: "Phase 5: Integration & polish — dev proxy, streaming responses, error handling, FAQ admin panel"
    status: completed
  - id: phase6-docs
    content: "Phase 6: Documentation — README.md setup guide, docs/PIPELINE.md AI design document"
    status: completed
isProject: false
---

# AI Customer Support Chatbot — Full-Stack Self-Learning Project

## Architecture Overview

```mermaid
flowchart TD
    User["User Browser"] -->|"HTTP"| Vue["Vue.js 3 (Vite)"]
    Vue -->|"REST API calls"| Django["Django REST Framework"]
    Django -->|"Read/Write"| Mongo["MongoDB\n(History + FAQ)"]
    Django -->|"RAG Pipeline"| AI["AI Module\n(LangChain)"]
    AI -->|"Embed query"| Embeddings["sentence-transformers\n(all-MiniLM-L6-v2)"]
    AI -->|"Similarity search"| Chroma["ChromaDB\n(Vector Store)"]
    AI -->|"Generate answer"| Ollama["Ollama\n(Mistral 7B)"]
    Chroma <-->|"Indexed from"| Mongo
```



## Tech Stack

- **Frontend**: Vue.js 3 (Composition API) + Vite + Pinia (state) + Tailwind CSS
- **Backend**: Python 3.11 + Django 5 + Django REST Framework
- **AI Pipeline**: LangChain + sentence-transformers + ChromaDB + Ollama (Mistral 7B)
- **Database**: MongoDB via MongoEngine ODM
- **Orchestration**: Docker Compose (MongoDB + backend + frontend)

## Project Structure

```
AI-Assistance/
├── frontend/             # Vue.js 3 app
│   ├── src/
│   │   ├── components/   # ChatWindow, MessageBubble, FAQPanel
│   │   ├── stores/       # Pinia chat store
│   │   └── views/        # HomeView
│   └── package.json
├── backend/              # Django project
│   ├── chatbot/          # Main Django app
│   │   ├── models.py     # Conversation, Message, FAQ (MongoEngine)
│   │   ├── views.py      # API endpoints
│   │   ├── serializers.py
│   │   └── ai_pipeline.py  # RAG logic
│   ├── requirements.txt
│   └── manage.py
├── docker-compose.yml
└── README.md
```

## AI Pipeline (RAG — Retrieval Augmented Generation)

```mermaid
sequenceDiagram
    participant U as User
    participant API as Django API
    participant RAG as RAG Pipeline
    participant Chroma as ChromaDB
    participant Ollama as Ollama LLM

    U->>API: POST /api/chat/ { message }
    API->>RAG: run_pipeline(message)
    RAG->>Chroma: embed(message) → similarity_search(top_k=3)
    Chroma-->>RAG: relevant FAQ context
    RAG->>Ollama: prompt = system + context + user_message
    Ollama-->>RAG: generated answer (stream)
    RAG-->>API: answer + sources
    API->>API: save to MongoDB history
    API-->>U: { answer, sources, conversation_id }
```



## REST API Endpoints

- `POST /api/chat/` — send message, get AI answer
- `GET /api/conversations/` — list all conversations
- `GET /api/conversations/{id}/` — fetch full conversation history
- `POST /api/faq/` — create FAQ entry (admin seeding)
- `GET /api/faq/` — list FAQ entries
