"""
Teams Bot module - Azure Communication Services Call Automation wrapper.

Handles joining/leaving Teams meetings and processing call events.
"""
import logging
from typing import Optional, Dict, Any
from azure.communication.callautomation import CallAutomationClient
from azure.communication.identity import CommunicationIdentityClient
from .config import settings

logger = logging.getLogger(__name__)


class TeamsBot:
    """Manages Teams meeting interactions via Azure Communication Services."""
    
    def __init__(self):
        """Initialize the Teams bot with ACS credentials."""
        self._client: Optional[CallAutomationClient] = None
        self._identity_client: Optional[CommunicationIdentityClient] = None
        self._bot_user_id: Optional[str] = None
        self._initialized = False
        self._init_error: Optional[str] = None
        self._try_initialize()
    
    def _try_initialize(self):
        """Attempt to initialize the ACS clients and create a bot identity."""
        if not settings.acs_connection_string:
            self._init_error = "ACS_CONNECTION_STRING not configured"
            logger.warning("TeamsBot: %s", self._init_error)
            return
        
        try:
            # Initialize Call Automation client
            self._client = CallAutomationClient.from_connection_string(
                settings.acs_connection_string
            )
            
            # Initialize Identity client and create a bot user
            self._identity_client = CommunicationIdentityClient.from_connection_string(
                settings.acs_connection_string
            )
            user = self._identity_client.create_user()
            self._bot_user_id = user.properties["id"]
            
            # Re-create the CallAutomationClient with the bot's source identity
            from azure.communication.callautomation._shared.models import CommunicationUserIdentifier
            self._client = CallAutomationClient.from_connection_string(
                settings.acs_connection_string,
                source=CommunicationUserIdentifier(self._bot_user_id),
            )
            
            self._initialized = True
            logger.info("TeamsBot: ACS initialized. Bot user: %s", self._bot_user_id)
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
            "bot_user_id": self._bot_user_id,
        }
    
    def join_meeting(self, meeting_url: str) -> Dict[str, Any]:
        """
        Join a Teams meeting using its URL.
        
        Uses the ACS Call Automation REST API with a proper bot identity
        and TeamsMeetingLink to join an existing Teams meeting.
        
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
            import requests
            import hmac
            import hashlib
            import base64
            import json as json_mod
            from datetime import datetime, timezone
            from urllib.parse import urlparse
            
            callback_url = f"{settings.bot_callback_url}/teams/callback"
            
            # Parse ACS endpoint and access key from the connection string
            acs_endpoint = None
            acs_key = None
            for part in settings.acs_connection_string.split(";"):
                if part.startswith("endpoint="):
                    acs_endpoint = part[len("endpoint="):].rstrip("/")
                elif part.startswith("accesskey="):
                    acs_key = part[len("accesskey="):]
            
            if not acs_endpoint or not acs_key:
                return {"success": False, "error": "Could not parse ACS connection string"}
            
            api_url = f"{acs_endpoint}/calling/callConnections?api-version=2023-10-15"
            
            # Build the request body for joining a Teams meeting.
            # We use the bot's own identity as the target since 'targets' is required.
            body = {
                "targets": [
                    {
                        "kind": "communicationUser",
                        "communicationUser": {
                            "id": self._bot_user_id
                        }
                    }
                ],
                "sourceIdentity": {
                    "kind": "communicationUser",
                    "communicationUser": {
                        "id": self._bot_user_id
                    }
                },
                "sourceDisplayName": "RAG Agent Bot",
                "callbackUri": callback_url,
                "teamsMeetingLink": meeting_url,
            }
            
            # If we have an Azure App ID (Bot ID), add it as teamsAppSource
            # This is critical for the bot to be recognized by Teams tenant policies
            # if settings.azure_app_id:
            #     body["teamsAppSource"] = {"appId": settings.azure_app_id}
            
            logger.info("TeamsBot: Joining meeting payload: %s", json_mod.dumps(body))
            
            # Generate HMAC-SHA256 auth header for ACS REST API
            date_str = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
            parsed = urlparse(api_url)
            host = parsed.hostname
            path_and_query = parsed.path + ("?" + parsed.query if parsed.query else "")
            
            content = json_mod.dumps(body)
            content_hash = base64.b64encode(
                hashlib.sha256(content.encode('utf-8')).digest()
            ).decode('utf-8')
            
            string_to_sign = f"POST\n{path_and_query}\n{date_str};{host};{content_hash}"
            decoded_key = base64.b64decode(acs_key)
            signature = base64.b64encode(
                hmac.new(decoded_key, string_to_sign.encode('utf-8'), hashlib.sha256).digest()
            ).decode('utf-8')
            
            auth_header = (
                f"HMAC-SHA256 SignedHeaders=date;host;x-ms-content-sha256"
                f"&Signature={signature}"
            )
            
            headers = {
                "Content-Type": "application/json",
                "Date": date_str,
                "Host": host,
                "x-ms-content-sha256": content_hash,
                "Authorization": auth_header,
            }
            
            logger.info("TeamsBot: Joining meeting via REST API...")
            response = requests.post(api_url, headers=headers, data=content)
            
            if response.status_code in (200, 201):
                data = response.json()
                call_connection_id = data.get("callConnectionId", "unknown")
                
                logger.info(
                    "TeamsBot: Joined meeting. call_connection_id=%s",
                    call_connection_id
                )
                
                return {
                    "success": True,
                    "call_connection_id": call_connection_id,
                    "meeting_url": meeting_url,
                }
            else:
                error_detail = response.text[:500]
                logger.error("TeamsBot: ACS API error %d: %s", response.status_code, error_detail)
                return {
                    "success": False,
                    "error": f"ACS API error ({response.status_code}): {error_detail}"
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
        # ACS webhook events nest fields like callConnectionId and
        # resultInformation inside a "data" sub-object.
        inner = event_data.get("data", {})
        call_connection_id = inner.get("callConnectionId", event_data.get("callConnectionId", ""))
        
        logger.info(
            "TeamsBot: Received event type=%s call=%s",
            event_type, call_connection_id
        )
        
        # Log full event for debugging
        import json as json_mod
        logger.info("TeamsBot: Full event: %s", json_mod.dumps(event_data, indent=2, default=str))
        
        result = {
            "event_type": event_type,
            "call_connection_id": call_connection_id,
            "action": "none",
        }
        
        if event_type == "Microsoft.Communication.CallConnected":
            result["action"] = "call_connected"
            logger.info("TeamsBot: Call connected successfully")
        
        elif event_type == "Microsoft.Communication.CreateCallFailed":
            result["action"] = "create_call_failed"
            result_info = inner.get("resultInformation", {})
            logger.error(
                "TeamsBot: CREATE CALL FAILED! Code: %s, SubCode: %s, Message: %s",
                result_info.get("code", "?"),
                result_info.get("subCode", "?"),
                result_info.get("message", "unknown")
            )
            
        elif event_type == "Microsoft.Communication.CallDisconnected":
            result["action"] = "call_disconnected"
            result_info = inner.get("resultInformation", {})
            code = result_info.get("code")
            sub_code = result_info.get("subCode")
            message = result_info.get("message", "unknown")
            
            if event_type == "Microsoft.Communication.CreateCallFailed":
                result["action"] = "create_call_failed"
                if code is None:
                    logger.error("TeamsBot: CREATE CALL FAILED! NO resultInformation found. Full event data: %s", json_mod.dumps(event_data, indent=2, default=str))
                else:
                    logger.error(
                        "TeamsBot: CREATE CALL FAILED! Code: %s, SubCode: %s, Message: %s",
                        code, sub_code, message
                    )
            else: # Microsoft.Communication.CallDisconnected
                result["action"] = "call_disconnected"
                if code is None:
                    logger.info("TeamsBot: Call disconnected. NO resultInformation found. Full event data: %s", json_mod.dumps(event_data, indent=2, default=str))
                else:
                    logger.info(
                        "TeamsBot: Call disconnected. Code: %s, SubCode: %s, Message: %s",
                        code, sub_code, message
                    )
            
        elif event_type == "Microsoft.Communication.ParticipantsUpdated":
            participants = inner.get("participants", [])
            result["action"] = "participants_updated"
            result["participant_count"] = len(participants)
            
        elif event_type == "Microsoft.Communication.PlayCompleted":
            result["action"] = "play_completed"
            
        elif event_type == "Microsoft.Communication.RecognizeCompleted":
            # Speech recognition result from ACS
            speech_result = inner.get("recognitionResult", {})
            result["action"] = "speech_recognized"
            result["speech_text"] = speech_result.get("speech", "")
            
        elif event_type == "Microsoft.Communication.RecognizeFailed":
            result["action"] = "speech_failed"
            result["error"] = inner.get("resultInformation", {}).get("message", "Unknown error")
        
        return result
