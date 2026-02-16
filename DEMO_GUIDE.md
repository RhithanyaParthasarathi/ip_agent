# Quick Start Guide - RAG Agent Demo

This guide will help you quickly set up and demo the RAG agent for your faculty guide.

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Dependencies

```powershell
# Install Python packages
pip install -r requirements.txt

# Install frontend packages
cd frontend
npm install
cd ..
```

### Step 2: Configure API Key

1. Copy `.env.example` to `.env`
2. Get your Anthropic API key from: https://console.anthropic.com/
3. Add it to `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

### Step 3: Verify Setup

```powershell
python setup_check.py
```

This will check if everything is configured correctly.

## 🎬 Running for Demo

You need **3 terminal windows**. Open them all before starting.

### Terminal 1: Start Qdrant
```powershell
docker run -p 6333:6333 qdrant/qdrant
```

Wait until you see: "Qdrant is ready to serve traffic"

### Terminal 2: Start Backend
```powershell
python main.py
```

Wait until you see: "Uvicorn running on http://0.0.0.0:8000"

### Terminal 3: Start Frontend
```powershell
cd frontend
npm run dev
```

Wait until you see: "Local: http://localhost:5173/"

## 🎯 Demo Flow for Faculty Guide

### Part 1: Introduction (2 minutes)

**Opening Statement:**
"I've built a RAG (Retrieval-Augmented Generation) agent that can answer questions using company documents while also handling general queries."

**Tech Stack to Mention:**
- Backend: Python, FastAPI, LangChain
- LLM: Anthropic Claude (Sonnet)
- Vector Database: Qdrant
- Frontend: React with Vite
- Embeddings: Sentence-Transformers

### Part 2: System Architecture (2 minutes)

**Explain the RAG Pipeline:**
1. Documents are uploaded through the UI
2. Text is split into chunks (1000 characters with 200 overlap)
3. Chunks are converted to embeddings using Sentence-Transformers
4. Embeddings are stored in Qdrant vector database
5. User asks a question
6. Question is converted to embedding
7. Qdrant finds the most similar chunks (top 5)
8. Context + Question sent to Claude
9. Claude generates answer with citations

**Show on screen:**
- Open Qdrant Dashboard: http://localhost:6333/dashboard
- Show API documentation: http://localhost:8000/docs

### Part 3: Live Demo (5 minutes)

**Step 1 - Show Empty State**
- Open http://localhost:5173
- Show the clean, modern interface
- Point out the empty knowledge base (0 documents)

**Step 2 - Upload a Document**
- Click "Choose File" in the sidebar
- Upload a sample PDF (e.g., a company policy document or any PDF)
- Show the processing message
- Point out the document count increase in the sidebar

**Step 3 - RAG Mode Demonstration**
- Ask a question about the uploaded document
- Example: "What are the main topics covered in this document?"
- Show the response appears with:
  - ✓ "From Documents" badge (RAG mode)
  - ✓ Source citations button
- Click to expand sources, show document excerpts

**Step 4 - General Knowledge Mode**
- Ask a general question unrelated to the document
- Example: "Explain what a neural network is"
- Show the response with:
  - ✓ "General Knowledge" badge
  - ✓ No sources (using Claude's knowledge)

**Step 5 - Conversation Context**
- Ask a follow-up question: "Can you elaborate on that?"
- Show that the system maintains conversation context

**Step 6 - Clear and Reset**
- Click "Clear" button
- Show conversation resets

### Part 4: Technical Features (2 minutes)

**Backend API:**
- Open http://localhost:8000/docs
- Show the FastAPI Swagger documentation
- Point out the endpoints:
  - POST /ask (conversational queries)
  - POST /upload/document (file uploads)
  - GET /collection/info (statistics)
  - POST /clear-memory (reset conversation)

**Vector Database:**
- Open http://localhost:6333/dashboard
- Show the "company_docs" collection
- Show vector count and points count
- Explain: Each point is a chunk with embedding

**Code Structure:**
- Briefly show the project structure
- Highlight key files:
  - `rag_agent.py` - Core RAG logic
  - `vector_store.py` - Qdrant integration
  - `document_processor.py` - Document chunking
  - `main.py` - FastAPI server
  - `frontend/src/` - React components

### Part 5: Key Features & Benefits (2 minutes)

**Key Features:**
1. ✅ Hybrid Mode: RAG + General Knowledge
2. ✅ Multiple Document Formats: PDF, DOCX, TXT, HTML
3. ✅ Source Citations: Transparency in answers
4. ✅ Conversation Memory: Context-aware responses
5. ✅ Modern UI: Clean, intuitive interface
6. ✅ REST API: Easy integration with other systems
7. ✅ Scalable: Qdrant handles millions of vectors

**Benefits:**
- Reduces manual document searching
- Provides accurate, cited answers
- Handles both specific and general queries
- Easy to add more documents
- Cost-effective (~$10-50/month for moderate use)

### Part 6: Future Enhancements (1 minute)

**Potential Next Steps:**
- [ ] User authentication and authorization
- [ ] Multi-language support
- [ ] Advanced filters (by date, department, etc.)
- [ ] Document management (delete, update)
- [ ] Analytics dashboard
- [ ] Integration with company systems
- [ ] Streaming responses for faster UX
- [ ] Export conversation history

## 📝 Demo Script Cheat Sheet

**Before Demo:**
- [ ] All 3 services running (Qdrant, Backend, Frontend)
- [ ] Have a sample PDF ready to upload
- [ ] Clear browser cache if needed
- [ ] Test the upload once before the actual demo

**During Demo:**
- [ ] Speak clearly about the problem being solved
- [ ] Show the architecture diagram (if you have one)
- [ ] Upload document and wait for confirmation
- [ ] Ask 2-3 questions from the document
- [ ] Ask 1-2 general questions
- [ ] Show the technical components (API docs, Qdrant)
- [ ] Highlight the code structure briefly

**Questions Faculty Might Ask:**

**Q: "Why use RAG instead of fine-tuning?"**
A: RAG is more flexible and cost-effective. Documents can be updated without retraining. Fine-tuning is expensive and time-consuming.

**Q: "How does it handle documents with different formats?"**
A: We use LangChain's document loaders that handle PDF, DOCX, TXT, HTML. The system extracts text and chunks it uniformly regardless of format.

**Q: "What's the accuracy?"**
A: Accuracy depends on document quality and question clarity. Claude Sonnet provides high-quality answers, and source citations allow users to verify.

**Q: "Can it scale?"**
A: Yes! Qdrant can handle millions of vectors. Claude API scales automatically. For very high traffic, we'd deploy multiple FastAPI instances behind a load balancer.

**Q: "What about costs?"**
A: Claude API costs ~$0.003-0.03 per 1K tokens. Typical query costs $0.01-0.05. For 1000 queries/month, expect $10-50. Qdrant is free (self-hosted).

**Q: "Is the data secure?"**
A: Currently using Anthropic's API (data sent to Claude). For sensitive data, we could use local LLMs like Llama or deploy Claude on private cloud.

## 🎓 Tips for Success

1. **Practice Once**: Run through the demo once before showing faculty
2. **Keep It Simple**: Focus on the user experience first, then dive into technical details
3. **Be Prepared for Delays**: API calls may take 2-3 seconds, mention this is normal
4. **Show Enthusiasm**: This is impressive work, be confident!
5. **Have Backup**: If something fails, you have the API docs and code to show

## 🆘 Troubleshooting During Demo

**If Qdrant won't start:**
- Check if Docker is running
- Try: `docker ps` to see containers
- Alternative: Show the API docs and code structure

**If Backend fails:**
- Check if API key is correct in `.env`
- Show error message and explain (shows debugging skills!)
- Fall back to showing code and architecture

**If Frontend won't load:**
- Check if backend is running first
- Try: `npm run dev` again
- Fall back to using API docs at http://localhost:8000/docs

**If Upload fails:**
- Check file format is supported
- Try a different file
- Use the `/upload/text` endpoint via API docs as backup

## ✅ Post-Demo

**What To Highlight:**
- Full-stack application (Backend + Frontend)
- Production-ready architecture
- Modern tech stack
- Clear code structure
- Comprehensive documentation

**Files to Show If Asked:**
- `README.md` - Complete documentation
- `rag_agent.py` - Core RAG logic
- `frontend/src/components/ChatInterface.jsx` - Main UI component

Good luck with your demo! 🚀
