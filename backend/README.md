# RAG Agent Backend

A FastAPI-based backend for a Retrieval-Augmented Generation (RAG) agent that answers questions from uploaded company documents and general knowledge, powered by Google Gemini and Qdrant vector database.

## Tech Stack

- **LLM**: Google Gemini 2.5 Flash (`gemini-2.5-flash`)
- **Embeddings**: Google Generative AI Embeddings (`gemini-embedding-001`)
- **Vector Database**: Qdrant (Docker)
- **Framework**: FastAPI + Uvicorn
- **Orchestration**: LangChain

## Prerequisites

- Python 3.10+
- Docker Desktop (for Qdrant)
- Google Gemini API key ([Get one free](https://aistudio.google.com/apikey))

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/RhithanyaParthasarathi/ip_agent.git
cd ip_agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
pip install langchain-qdrant langchain-text-splitters
```

### 4. Start Qdrant (Docker)

```bash
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant
```

### 5. Configure environment variables

Create a `backend/.env` file:

```env
GOOGLE_API_KEY=your_google_api_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
APP_NAME=Company RAG Agent
UPLOAD_DIR=./data/uploads
```

### 6. Run the backend

```bash
cd backend
python main.py
```

The server will start at `http://localhost:8000`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root / status |
| `GET` | `/health` | Health check |
| `POST` | `/ask` | Ask a question (`{ "question": "..." }`) |
| `POST` | `/upload/document` | Upload a file (PDF, DOCX, TXT, HTML) |
| `POST` | `/upload/text` | Upload raw text (`{ "text": "...", "source": "..." }`) |
| `GET` | `/collection/info` | Vector store stats |
| `POST` | `/clear-memory` | Clear conversation history |
| `DELETE` | `/collection` | Delete all documents from vector store |

## Project Structure

```
backend/
├── .env                  # Environment variables
├── config.py             # Pydantic settings
├── main.py               # FastAPI app & routes
├── rag_agent.py          # RAG agent logic (LLM + retriever chain)
├── vector_store.py       # Qdrant vector store manager
├── document_processor.py # Document chunking & processing
├── requirements.txt      # Python dependencies
└── data/uploads/         # Uploaded documents storage
```

## How It Works

1. **Upload documents** via `/upload/document` — files are chunked (1000 chars, 200 overlap) and embedded into Qdrant
2. **Ask questions** via `/ask` — the agent retrieves relevant chunks from Qdrant and uses them as context for Gemini
3. If no relevant documents are found, the agent falls back to **general knowledge** mode
4. Responses include source attribution and mode indicator (RAG vs General)
