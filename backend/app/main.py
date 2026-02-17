"""FastAPI application for the RAG agent."""
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .rag_agent import RAGAgent
from .teams_bot import TeamsBot
from .speech_service import SpeechService
from .call_manager import CallManager
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="RAG Agent API with Google Gemini, Qdrant, and Teams Integration",
    version="2.0.0"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173","http://localhost:5174" ],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
agent = RAGAgent()
teams_bot = TeamsBot()
speech_service = SpeechService()
call_manager = CallManager(teams_bot, speech_service, agent)


# ─── Pydantic models ───

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


class JoinMeetingRequest(BaseModel):
    meeting_url: str


# ─── Existing RAG API Routes ───

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "2.0.0",
        "status": "running",
        "features": ["rag", "teams"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    collection_info = agent.get_collection_info()
    return {
        "status": "healthy",
        "vector_store": collection_info,
        "teams_bot": teams_bot.get_status(),
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
    """Clear the conversation memory."""
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


# ─── Teams Integration Routes ───

@app.get("/teams/status")
async def teams_status():
    """Get the Teams bot status and active calls."""
    return call_manager.get_status()


@app.post("/teams/join")
async def join_meeting(request: JoinMeetingRequest):
    """Join a Teams meeting by URL."""
    if not teams_bot.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Teams bot is not configured. Check ACS_CONNECTION_STRING."
        )
    
    result = call_manager.join_meeting(request.meeting_url)
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to join meeting"))


@app.post("/teams/leave/{call_connection_id}")
async def leave_meeting(call_connection_id: str):
    """Leave an active Teams meeting."""
    result = call_manager.leave_meeting(call_connection_id)
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to leave meeting"))


@app.post("/teams/callback")
async def teams_callback(request: Request):
    """
    ACS Call Automation webhook callback.
    
    Azure sends call events (connected, disconnected, speech recognized, etc.)
    to this endpoint.
    """
    try:
        body = await request.json()
        
        # ACS sends events as a list
        if isinstance(body, list):
            results = []
            for event in body:
                result = call_manager.handle_call_event(event)
                results.append(result)
            return {"events_processed": len(results), "results": results}
        else:
            result = call_manager.handle_call_event(body)
            return result
            
    except Exception as e:
        logger.error("Teams callback error: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/teams/call/{call_connection_id}")
async def get_call_info(call_connection_id: str):
    """Get info about a specific active call."""
    info = call_manager.get_call_info(call_connection_id)
    if info:
        return info
    raise HTTPException(status_code=404, detail="Call not found")


@app.get("/teams/events/{call_connection_id}")
async def get_call_events(call_connection_id: str, since: int = 0):
    """Get events for a call, optionally since a given event index."""
    events = call_manager.get_call_events(call_connection_id, since)
    return {"events": events, "count": len(events)}


# ─── Teams Text Query (for demo without full audio pipeline) ───

@app.post("/teams/ask")
async def teams_ask(request: QuestionRequest):
    """
    Ask a question through the Teams context.
    
    This is a convenience endpoint for the demo — it uses the same 
    RAG agent but logs the interaction as if it came from a Teams call.
    Useful for testing the pipeline without full audio setup.
    """
    try:
        result = agent.ask(
            request.question,
            conversation_id=request.conversation_id,
            selected_sources=request.selected_sources
        )
        return {
            **result,
            "channel": "teams",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
