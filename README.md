# Company RAG Agent

A production-ready RAG (Retrieval-Augmented Generation) agent built with Claude (Anthropic), Qdrant vector database, FastAPI backend, and React frontend. The agent can answer questions using company documents (RAG mode) or general knowledge.

## 🎯 Features

- **Hybrid Q&A**: Answers questions using company documents OR general knowledge
- **Modern UI**: Beautiful React-based chat interface
- **Document Support**: PDF, DOCX, TXT, HTML files
- **Vector Search**: Fast similarity search with Qdrant
- **Conversational Memory**: Maintains context across conversations
- **REST API**: FastAPI backend for easy integration
- **Source Citations**: View document sources for each answer
- **LLM**: Claude Sonnet for high-quality responses

## 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- Anthropic API key
- Docker (for Qdrant)

## 🚀 Quick Setup

### 1. Backend Setup

Install Python dependencies:
```powershell
pip install -r requirements.txt
```

### 2. Setup Qdrant Vector Database

**Run Qdrant using Docker (Recommended)**:
```powershell
docker run -p 6333:6333 qdrant/qdrant
```

### 3. Configure Environment

Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

Get your API key from: https://console.anthropic.com/

### 4. Frontend Setup

Navigate to frontend directory and install dependencies:
```powershell
cd frontend
npm install
cd ..
```

### 5. Run the Application

You need 3 terminals:

**Terminal 1 - Qdrant:**
```powershell
docker run -p 6333:6333 qdrant/qdrant
```

**Terminal 2 - Backend:**
```powershell
python main.py
```

**Terminal 3 - Frontend:**
```powershell
cd frontend
npm run dev
```

### 6. Access the Application

- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 🎮 Usage

### Option 1: Web Interface (Recommended)

1. **Access**: Open http://localhost:5173 in your browser
2. **Upload Documents**: Click "Choose File" in the sidebar to upload company documents
3. **Ask Questions**: Type your question in the chat interface
4. **View Sources**: Click on source citations to see document excerpts
5. **Clear Chat**: Use the "Clear" button to start a new conversation

The interface shows:
- 📚 **From Documents** badge: Answer comes from your uploaded documents (RAG mode)
- 🌐 **General Knowledge** badge: Answer from Claude's general knowledge

### Option 2: Simple Python Script

```python
from rag_agent import RAGAgent

# Initialize agent
agent = RAGAgent()

# Add documents
agent.add_documents("path/to/document.pdf")

# Add text
agent.add_text("Company info here...", source="company_data")

# Ask questions
response = agent.ask("What are the working hours?")
print(response['answer'])
```

### Option 3: REST API

Start the FastAPI server:
```bash
python main.py
```

The server runs at `http://localhost:8000`

**API Documentation**: http://localhost:8000/docs

**Key Endpoints:**
- `POST /ask` - Ask a question
- `POST /upload/document` - Upload a document (PDF, DOCX, TXT)
- `POST /upload/text` - Upload raw text
- `GET /collection/info` - Get vector store stats
- `POST /clear-memory` - Clear conversation history

**Example API Usage:**
```bash
# Ask a question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the company benefits?"}'

# Upload a document
curl -X POST "http://localhost:8000/upload/document" \
  -F "file=@document.pdf"
```

## 📁 Project Structure

```
ip/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── rag_agent.py           # Main RAG agent logic
│   ├── vector_store.py        # Qdrant vector store manager
│   ├── document_processor.py  # Document loading and chunking
│   ├── config.py              # Configuration settings
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx  # Main chat component
│   │   │   ├── Sidebar.jsx        # Document upload sidebar
│   │   │   ├── Message.jsx        # Message display
│   │   │   └── Header.jsx         # App header
│   │   ├── App.jsx            # Main app component
│   │   └── main.jsx           # Entry point
│   ├── package.json           # Node dependencies
│   └── vite.config.js         # Vite configuration
├── data/
│   └── uploads/              # Uploaded documents
├── .env                      # Environment variables (create this)
├── .env.example             # Environment template
└── README.md                # This file
```

## 🔧 Configuration

Edit `config.py` or `.env` to customize:

- **Embedding Model**: Default is `all-MiniLM-L6-v2` (fast, free)
- **Claude Model**: Default is `claude-3-sonnet-20240229`
- **Chunk Size**: Default 1000 characters
- **Top K Results**: Default 5 documents retrieved

## 📝 Adding Your Documents

### Method 1: Python Script
```python
agent = RAGAgent()
agent.add_documents("data/uploads/company_handbook.pdf")
agent.add_documents("data/uploads/policies.docx")
```

### Method 2: API Endpoint
```bash
curl -X POST "http://localhost:8000/upload/document" \
  -F "file=@company_handbook.pdf"
```

### Method 3: Bulk Upload
Place files in `data/uploads/` and run:
```python
from pathlib import Path
from rag_agent import RAGAgent

agent = RAGAgent()
upload_dir = Path("data/uploads")

for file in upload_dir.glob("*.*"):
    if file.suffix in [".pdf", ".docx", ".txt"]:
        print(f"Processing {file.name}...")
        agent.add_documents(str(file))
```

## 🧪 Testing

The agent operates in two modes:

1. **RAG Mode**: Uses retrieved documents to answer
2. **General Mode**: Uses Claude's general knowledge

The agent automatically determines which mode to use based on the question and available context.

## 🔍 Troubleshooting

### Qdrant Connection Error
```
Error: Could not connect to Qdrant
```
**Solution**: Make sure Qdrant is running:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### Anthropic API Error
```
Error: Invalid API key
```
**Solution**: Check your `.env` file has the correct API key:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### Import Errors
```
ModuleNotFoundError: No module named 'langchain'
```
**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

## 💰 Cost Estimation

**Free Components:**
- Qdrant (local): $0
- Embeddings model: $0
- Python/FastAPI: $0

**Paid Components:**
- Claude API: ~$0.003-0.03 per 1K tokens
- Typical query: ~$0.01-0.05

**Monthly estimate** (1000 queries): $10-50

## 🚢 Deployment

### Local Development
```bash
python main.py
```

### Production (Docker)
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t rag-agent .
docker run -p 8000:8000 --env-file .env rag-agent
```

## 🎓 Demo for Faculty Guide

To showcase the RAG agent system:

### What to Show

1. **System Architecture**
   - Explain the RAG pipeline: Document → Chunks → Embeddings → Vector DB → Retrieval → LLM → Answer
   - Tech stack: Claude (LLM), Qdrant (Vector DB), LangChain (Framework), FastAPI + React

2. **Document Upload**
   - Upload a sample company document (PDF/DOCX)
   - Show the chunking process and vector count increase

3. **RAG Mode Demonstration**
   - Ask questions about the uploaded document
   - Show the "From Documents" badge
   - Display source citations with document excerpts

4. **General Knowledge Mode**
   - Ask general questions (e.g., "What is machine learning?")
   - Show the "General Knowledge" badge
   - Demonstrate the hybrid capability

5. **Technical Features**
   - Show the FastAPI documentation at `/docs`
   - Display the Qdrant dashboard with vector statistics
   - Demonstrate conversation memory (context retention)

### Talking Points

- **Problem Solved**: Traditional chatbots can't answer company-specific questions. RAG combines document knowledge with LLM capabilities.
- **Scalability**: Qdrant handles millions of documents efficiently
- **Cost-Effective**: Only pay for LLM usage (~$10-50/month for moderate use)
- **Production-Ready**: FastAPI backend, React frontend, Docker deployment
- **Extensible**: Easy to add more document types, switch LLMs, or deploy to cloud

## 📚 Next Steps

1. ✅ Setup the environment
2. ✅ Upload company documents via the UI
3. ✅ Test RAG queries through the chat interface
4. ⬜ Customize the UI styling and branding
5. ⬜ Deploy to production
6. ⬜ Add authentication
7. ⬜ Monitor usage and costs

## 🤝 Support

For issues or questions, check:
- Qdrant docs: https://qdrant.tech/documentation/
- LangChain docs: https://python.langchain.com/
- Anthropic docs: https://docs.anthropic.com/

## 📄 License

MIT License - Feel free to modify and use for your company.