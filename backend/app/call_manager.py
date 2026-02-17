"""
Call Manager module - Orchestrates active calls and the audio pipeline.

Tracks call state, manages events, and wires audio through STT → RAG → TTS.
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from .teams_bot import TeamsBot
from .speech_service import SpeechService
from .rag_agent import RAGAgent

logger = logging.getLogger(__name__)


@dataclass
class CallEvent:
    """A single event in a call's lifecycle."""
    timestamp: str
    event_type: str
    message: str
    data: Optional[Dict[str, Any]] = None


@dataclass
class ActiveCall:
    """Represents an active Teams meeting session."""
    call_connection_id: str
    meeting_url: str
    status: str = "connecting"  # connecting, connected, disconnected, error
    joined_at: str = ""
    participant_count: int = 0
    events: List[CallEvent] = field(default_factory=list)
    transcript: List[Dict[str, str]] = field(default_factory=list)
    
    def add_event(self, event_type: str, message: str, data: Dict = None):
        """Add an event to the call log."""
        event = CallEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            message=message,
            data=data,
        )
        self.events.append(event)
        # Keep last 100 events
        if len(self.events) > 100:
            self.events = self.events[-100:]
    
    def add_transcript_entry(self, speaker: str, text: str, is_bot: bool = False):
        """Add a transcript entry."""
        self.transcript.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "text": text,
            "is_bot": is_bot,
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the call to a dictionary."""
        return {
            "call_connection_id": self.call_connection_id,
            "meeting_url": self.meeting_url,
            "status": self.status,
            "joined_at": self.joined_at,
            "participant_count": self.participant_count,
            "event_count": len(self.events),
            "recent_events": [
                {
                    "timestamp": e.timestamp,
                    "event_type": e.event_type,
                    "message": e.message,
                }
                for e in self.events[-10:]
            ],
            "transcript": self.transcript[-20:],
        }


class CallManager:
    """Orchestrates calls: Teams bot + Speech + RAG agent."""
    
    def __init__(self, teams_bot: TeamsBot, speech_service: SpeechService, rag_agent: RAGAgent):
        self.teams_bot = teams_bot
        self.speech_service = speech_service
        self.rag_agent = rag_agent
        self.active_calls: Dict[str, ActiveCall] = {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall status."""
        return {
            "bot_status": self.teams_bot.get_status(),
            "speech_status": self.speech_service.get_status(),
            "active_calls": [
                call.to_dict() for call in self.active_calls.values()
            ],
            "total_active_calls": len(self.active_calls),
        }
    
    def join_meeting(self, meeting_url: str) -> Dict[str, Any]:
        """Join a Teams meeting and start tracking it."""
        result = self.teams_bot.join_meeting(meeting_url)
        
        if result.get("success"):
            call_id = result["call_connection_id"]
            call = ActiveCall(
                call_connection_id=call_id,
                meeting_url=meeting_url,
                status="connecting",
                joined_at=datetime.now().isoformat(),
            )
            call.add_event("join_requested", f"Joining meeting: {meeting_url}")
            self.active_calls[call_id] = call
            
            return {
                "success": True,
                "call_connection_id": call_id,
                "status": "connecting",
            }
        
        return result
    
    def leave_meeting(self, call_connection_id: str) -> Dict[str, Any]:
        """Leave a meeting and clean up."""
        result = self.teams_bot.leave_meeting(call_connection_id)
        
        if call_connection_id in self.active_calls:
            call = self.active_calls[call_connection_id]
            call.status = "disconnected"
            call.add_event("leave_requested", "Bot leaving meeting")
        
        return result
    
    def handle_call_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a call event from ACS webhook."""
        result = self.teams_bot.handle_event(event_data)
        
        call_id = result.get("call_connection_id", "")
        action = result.get("action", "none")
        
        # Get or create call record
        call = self.active_calls.get(call_id)
        if not call:
            logger.warning("CallManager: Event for unknown call %s", call_id)
            return result
        
        # Update call state based on event
        if action == "call_connected":
            call.status = "connected"
            call.add_event("connected", "Bot connected to meeting")
            
        elif action == "call_disconnected":
            call.status = "disconnected"
            call.add_event("disconnected", "Bot disconnected from meeting")
            
        elif action == "participants_updated":
            count = result.get("participant_count", 0)
            call.participant_count = count
            call.add_event("participants", f"Participants updated: {count}")
            
        elif action == "speech_recognized":
            speech_text = result.get("speech_text", "")
            if speech_text:
                call.add_transcript_entry("Participant", speech_text, is_bot=False)
                call.add_event("speech", f"Heard: {speech_text[:50]}...")
                
                # Process through RAG agent
                self._process_voice_query(call, speech_text)
        
        return result
    
    def _process_voice_query(self, call: ActiveCall, question: str):
        """Process a voice query through the RAG pipeline."""
        try:
            call.add_event("processing", f"Processing question: {question[:50]}...")
            
            # Get answer from RAG agent
            rag_result = self.rag_agent.ask(question)
            answer = rag_result.get("answer", "I couldn't generate an answer.")
            mode = rag_result.get("mode", "general")
            
            # Add to transcript
            call.add_transcript_entry(
                "RAG Bot",
                answer,
                is_bot=True,
            )
            
            call.add_event(
                "answered",
                f"Answered ({mode}): {answer[:50]}...",
                {"mode": mode, "source_count": len(rag_result.get("sources", []))},
            )
            
            # TODO: When Google Cloud TTS is configured, synthesize and play audio
            # audio_bytes = self.speech_service.synthesize_speech(answer)
            # self.teams_bot.play_audio(call.call_connection_id, audio_bytes)
            
            logger.info("CallManager: Processed voice query for call %s", call.call_connection_id)
            
        except Exception as e:
            error_msg = f"Error processing voice query: {str(e)}"
            logger.error("CallManager: %s", error_msg)
            call.add_event("error", error_msg)
    
    def get_call_info(self, call_connection_id: str) -> Optional[Dict[str, Any]]:
        """Get info about a specific call."""
        call = self.active_calls.get(call_connection_id)
        if call:
            return call.to_dict()
        return None
    
    def get_call_events(self, call_connection_id: str, since: int = 0) -> List[Dict]:
        """Get events for a call, optionally since a given index."""
        call = self.active_calls.get(call_connection_id)
        if not call:
            return []
        return [
            {
                "timestamp": e.timestamp,
                "event_type": e.event_type,
                "message": e.message,
            }
            for e in call.events[since:]
        ]
