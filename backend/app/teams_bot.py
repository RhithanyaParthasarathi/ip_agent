"""
Teams Bot module - Azure Communication Services Call Automation wrapper.

Handles joining/leaving Teams meetings and processing call events.
"""
import logging
from typing import Optional, Dict, Any
from azure.communication.callautomation import (
    CallAutomationClient,
    CallInvite,
    GroupCallLocator,
    ServerCallLocator,
)
from azure.communication.callautomation.aio import CallAutomationClient as AsyncCallAutomationClient
from .config import settings

logger = logging.getLogger(__name__)


class TeamsBot:
    """Manages Teams meeting interactions via Azure Communication Services."""
    
    def __init__(self):
        """Initialize the Teams bot with ACS credentials."""
        self._client: Optional[CallAutomationClient] = None
        self._initialized = False
        self._init_error: Optional[str] = None
        self._try_initialize()
    
    def _try_initialize(self):
        """Attempt to initialize the ACS client."""
        if not settings.acs_connection_string:
            self._init_error = "ACS_CONNECTION_STRING not configured"
            logger.warning("TeamsBot: %s", self._init_error)
            return
        
        try:
            self._client = CallAutomationClient.from_connection_string(
                settings.acs_connection_string
            )
            self._initialized = True
            logger.info("TeamsBot: ACS client initialized successfully")
        except Exception as e:
            self._init_error = f"Failed to initialize ACS client: {str(e)}"
            logger.error("TeamsBot: %s", self._init_error)
    
    @property
    def is_ready(self) -> bool:
        """Check if the bot is ready to make calls."""
        return self._initialized and self._client is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current bot status."""
        return {
            "initialized": self._initialized,
            "error": self._init_error,
            "acs_configured": bool(settings.acs_connection_string),
            "callback_url": settings.bot_callback_url,
        }
    
    def join_meeting(self, meeting_url: str) -> Dict[str, Any]:
        """
        Join a Teams meeting using its URL.
        
        Args:
            meeting_url: The Teams meeting join URL
            
        Returns:
            Dict with call_connection_id and status
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": self._init_error or "Bot not initialized"
            }
        
        try:
            callback_url = f"{settings.bot_callback_url}/teams/callback"
            
            # Create the call using Teams meeting URL
            call_connection = self._client.create_group_call(
                target_participant=None,
                callback_url=callback_url,
                teams_meeting_url=meeting_url,
            )
            
            call_connection_id = call_connection.call_connection_id
            
            logger.info(
                "TeamsBot: Joined meeting. call_connection_id=%s",
                call_connection_id
            )
            
            return {
                "success": True,
                "call_connection_id": call_connection_id,
                "meeting_url": meeting_url,
            }
            
        except Exception as e:
            error_msg = f"Failed to join meeting: {str(e)}"
            logger.error("TeamsBot: %s", error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def leave_meeting(self, call_connection_id: str) -> Dict[str, Any]:
        """
        Leave an active call/meeting.
        
        Args:
            call_connection_id: The call connection ID to hang up
            
        Returns:
            Dict with success status
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": self._init_error or "Bot not initialized"
            }
        
        try:
            call_connection = self._client.get_call_connection(call_connection_id)
            call_connection.hang_up(is_for_everyone=False)
            
            logger.info(
                "TeamsBot: Left meeting. call_connection_id=%s",
                call_connection_id
            )
            
            return {
                "success": True,
                "call_connection_id": call_connection_id,
            }
            
        except Exception as e:
            error_msg = f"Failed to leave meeting: {str(e)}"
            logger.error("TeamsBot: %s", error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def handle_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming ACS call event (webhook callback).
        
        Args:
            event_data: The event payload from ACS
            
        Returns:
            Dict with event type and any actions taken
        """
        event_type = event_data.get("type", "unknown")
        call_connection_id = event_data.get("callConnectionId", "")
        
        logger.info(
            "TeamsBot: Received event type=%s call=%s",
            event_type, call_connection_id
        )
        
        result = {
            "event_type": event_type,
            "call_connection_id": call_connection_id,
            "action": "none",
        }
        
        if event_type == "Microsoft.Communication.CallConnected":
            result["action"] = "call_connected"
            logger.info("TeamsBot: Call connected successfully")
            
        elif event_type == "Microsoft.Communication.CallDisconnected":
            result["action"] = "call_disconnected"
            logger.info("TeamsBot: Call disconnected")
            
        elif event_type == "Microsoft.Communication.ParticipantsUpdated":
            participants = event_data.get("participants", [])
            result["action"] = "participants_updated"
            result["participant_count"] = len(participants)
            
        elif event_type == "Microsoft.Communication.PlayCompleted":
            result["action"] = "play_completed"
            
        elif event_type == "Microsoft.Communication.RecognizeCompleted":
            # Speech recognition result from ACS
            speech_result = event_data.get("recognitionResult", {})
            result["action"] = "speech_recognized"
            result["speech_text"] = speech_result.get("speech", "")
            
        elif event_type == "Microsoft.Communication.RecognizeFailed":
            result["action"] = "speech_failed"
            result["error"] = event_data.get("resultInformation", {}).get("message", "Unknown error")
        
        return result
