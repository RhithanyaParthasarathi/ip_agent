# Setup Guide for Faculty Demo

## Quick Start (5 Minutes)

### Step 1: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### Step 2: Start Qdrant Database

**Using Docker (Recommended):**
```powershell
docker run -p 6333:6333 qdrant/qdrant
```

**OR using Docker Compose:**
```powershell
docker-compose up -d
```

If you don't have Docker, Qdrant can run embedded (no separate installation needed - will work automatically).

### Step 3: Configure API Key

1. Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```

2. Get your Anthropic API key:
   - Go to: https://console.anthropic.com/
   - Sign up/login
   - Create an API key
   - Add $5-10 credit to your account

3. Edit `.env` file and add your key:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

### Step 4: Run Demo

```powershell
python demo.py
```

This will show:
- ✓ Agent initialization
- ✓ Adding company data
- ✓ RAG-based questions (using company docs)
- ✓ General knowledge questions

### Step 5 (Optional): Start API Server

```powershell
python main.py
```

Visit http://localhost:8000/docs to see the interactive API documentation.

## What to Show Your Faculty Guide

### 1. **Architecture Overview**
- **LLM**: Claude by Anthropic (state-of-the-art reasoning)
- **Vector DB**: Qdrant (efficient similarity search)
- **Framework**: LangChain (production-ready RAG)
- **API**: FastAPI (modern REST API)

### 2. **Key Features Implemented**
- ✅ Document ingestion (PDF, DOCX, TXT, HTML)
- ✅ Text chunking and embedding
- ✅ Vector storage and retrieval
- ✅ RAG pipeline with Claude
- ✅ Hybrid mode (RAG + General knowledge)
- ✅ Conversational memory
- ✅ REST API with FastAPI

### 3. **Demo Flow**

**Show the demo.py output:**
```
1. Agent initializes successfully
2. Adds sample company data to vector store
3. Answers questions using RAG (with source citations)
4. Answers general questions without RAG
5. Shows what sources were used
```

**Show the API (if time permits):**
```
1. Open http://localhost:8000/docs
2. Try the POST /ask endpoint
3. Try uploading a document
4. Show the collection info
```

### 4. **Code Walkthrough**

**Core Components:**

1. **`config.py`** - Configuration management
2. **`vector_store.py`** - Qdrant integration, handles embeddings
3. **`document_processor.py`** - Document loading and chunking
4. **`rag_agent.py`** - Main RAG logic, LLM integration
5. **`main.py`** - FastAPI REST API

**Key Technical Points:**
- Uses sentence transformers for embeddings (free, local)
- Chunks documents with overlap for context
- Retrieves top-K most relevant chunks
- Combines retrieved context with Claude's reasoning
- Maintains conversation history

### 5. **Next Steps / Future Work**

**Current Status**: ✅ Backend complete (RAG + LLM)

**Remaining Work**:
- Frontend UI (React/Next.js)
- User authentication
- Document management interface
- Deployment to cloud
- Usage monitoring
- Cost optimization

**Why this approach?**
- Started with core functionality (RAG + LLM)
- Demonstrates working AI system
- Can add frontend/features incrementally
- Modular architecture for easy extension

## Troubleshooting

### If demo fails:

**Check 1: Qdrant running?**
```powershell
# Should show Qdrant UI
Start "http://localhost:6333/dashboard"
```

**Check 2: API key valid?**
```powershell
# Check .env file exists and has key
cat .env
```

**Check 3: Dependencies installed?**
```powershell
pip list | Select-String -Pattern "langchain|anthropic|qdrant"
```

### Quick Fixes

**Error: "Cannot connect to Qdrant"**
→ Run: `docker run -p 6333:6333 qdrant/qdrant`

**Error: "Invalid API key"**
→ Check `.env` file has correct `ANTHROPIC_API_KEY`

**Error: "Module not found"**
→ Run: `pip install -r requirements.txt`

## Contact Info

If you need help during the demo, the system logs errors to console. You can also check:
- `/collection/info` endpoint for vector store status
- `/health` endpoint for system health

## Talking Points for Faculty

1. **Problem**: Companies need AI agents that can answer from their documents AND general knowledge
2. **Solution**: Built hybrid RAG agent with Claude and Qdrant
3. **Technology**: Modern LLM stack with production-ready tools
4. **Status**: Core backend complete and working
5. **Demo**: Live demonstration of document Q&A
6. **Next**: Adding frontend and deploying to production
