"""FastAPI application for the RAG agent."""
import os
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .rag_agent import RAGAgent
from .config import settings


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="RAG Agent API with Google Gemini and Qdrant",
    version="1.0.0"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173","http://localhost:5174" ],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG agent
agent = RAGAgent()


# Pydantic models
class QuestionRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    selected_sources: Optional[List[str]] = None


class TextUploadRequest(BaseModel):
    text: str
    source: Optional[str] = "manual_input"
    conversation_id: Optional[str] = None


class QuestionResponse(BaseModel):
    answer: str
    sources: List[dict]
    mode: str


# API Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    collection_info = agent.get_collection_info()
    return {
        "status": "healthy",
        "vector_store": collection_info
    }


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question with optional conversation filtering."""
    try:
        result = agent.ask(
            request.question,
            conversation_id=request.conversation_id,
            selected_sources=request.selected_sources
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: str = Form(None)
):
    """Upload a document to a conversation's knowledge base."""
    try:
        file_path = settings.upload_dir / file.filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        result = agent.add_documents(str(file_path), conversation_id=conversation_id)
        
        if result["success"]:
            return {
                "message": "Document uploaded and processed successfully",
                "filename": file.filename,
                "chunks": result["chunks_created"]
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Error processing document: {result['error']}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/text")
async def upload_text(request: TextUploadRequest):
    """Upload raw text to the knowledge base."""
    try:
        result = agent.add_text(request.text, request.source, conversation_id=request.conversation_id)
        
        if result["success"]:
            return {
                "message": "Text uploaded and processed successfully",
                "chunks": result["chunks_created"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Error processing text: {result['error']}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear-memory")
async def clear_memory():
    """
    Clear the conversation memory.
    """
    agent.clear_memory()
    return {"message": "Conversation memory cleared"}


@app.get("/collection/info")
async def get_collection_info():
    """Get information about the vector store collection."""
    return agent.get_collection_info()


@app.get("/sources/{conversation_id}")
async def get_sources(conversation_id: str):
    """Get all uploaded sources for a conversation."""
    try:
        sources = agent.vector_store_manager.get_sources_for_conversation(conversation_id)
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sources/{conversation_id}/{source_name:path}")
async def delete_source(conversation_id: str, source_name: str):
    """Delete a specific source from a conversation."""
    try:
        deleted_count = agent.vector_store_manager.delete_source(conversation_id, source_name)
        return {
            "message": f"Deleted {deleted_count} chunks for '{source_name}'",
            "deleted_chunks": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
