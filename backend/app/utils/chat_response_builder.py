"""Utility for building and validating chat responses"""

import logging
from typing import Any, Dict

from fastapi.responses import JSONResponse

from app.schemas.chat_response import FullChatResponse, StructuredChatResponse

logger = logging.getLogger(__name__)
class ChatResponseBuilder:
    """Utility class for building chat responses in different formats"""
    
    @staticmethod
    def build_structured(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build MVP spec format from LangGraph output"""
        
        # Extract reply from LangGraph output
        reply = raw_data.get("agent_reply", "")
        if not reply:
            reply = raw_data.get("message", "")
        
        # Convert actions from object format to string array format
        actions_raw = raw_data.get("agent_actions", [])
        actions = []
        
        for action in actions_raw:
            if isinstance(action, dict):
                # Extract action type from nested structure
                action_type = action.get("type", "")
                if action_type:
                    actions.append(action_type)
                elif "action" in action:
                    actions.append(str(action["action"]))
            elif isinstance(action, str):
                actions.append(action)
        
        # Build response according to MVP spec
        response = {"reply": reply}
        
        # Only include actions array if there are actions
        if actions:
            response["actions"] = actions
        
        logger.info({
            "event": "chat_response_built",
            "format": "structured",
            "conversation_id": raw_data.get("conversation_id", "unknown"),
            "actions_count": len(actions),
            "response_size": len(str(response))
        })
        
        return response
    
    @staticmethod
    def build_full(raw_data: Dict[str, Any], conversation_id: str, auth: Dict[str, Any]) -> Dict[str, Any]:
        """Build full format for backward compatibility"""
        
        confidence = raw_data.get("confidence", 0.5)
        
        # Build comprehensive response
        response = {
            "reply": raw_data.get("agent_reply", ""),
            "confidence": confidence,
            "actions": raw_data.get("agent_actions", []),
            "intent": raw_data.get("agent_used", raw_data.get("intent", "")),
            "conversation_id": conversation_id,
            "requires_escalation": bool(raw_data.get("requires_escalation", False)),
            "metadata": raw_data.get("metadata", {}),
            "tenantId": auth.get("tenant_id", "")
        }
        
        logger.info({
            "event": "chat_response_built",
            "format": "full",
            "conversation_id": conversation_id,
            "actions_count": len(raw_data.get("agent_actions", [])),
            "response_size": len(str(response))
        })
        
        return response
    
    @staticmethod
    def extract_workflow_data(raw: dict) -> Dict[str, Any]:
        """Extract and format LangGraph output for both response formats"""
        
        # Extract basic response fields
        extracted = {
            "agent_reply": raw.get("agent_reply", ""),
            "agent_actions": raw.get("agent_actions", []),
            "agent_used": raw.get("agent_used", raw.get("intent", "")),
            "intent": raw.get("intent", {}),
            "confidence": raw.get("confidence", 0.5),
            "requires_escalation": raw.get("requires_escalation", False),
            "escalation_reason": raw.get("escalation_reason", ""),
            "rag_context": raw.get("rag_context", ""),
            "conversation_id": raw.get("conversation_id", ""),
            "moderated": raw.get("moderated", False),
            "intent_classified": raw.get("intent_classified", False),
            "agent_done": raw.get("agent_done", False),
            "safety_checked": raw.get("safety_checked", False),
            "metadata": {
                "channel": raw.get("channel", ""),
                "language": raw.get("language", "en"),
                "agent": raw.get("agent_used", ""),
                "intent_classification": raw.get("intent", {}),
                "rag_context_used": bool(raw.get("rag_context", "")),
                "graph_steps": {
                    "moderated": raw.get("moderated", False),
                    "classified": raw.get("intent_classified", False),
                    "agent_done": raw.get("agent_done", False),
                    "safety_checked": raw.get("safety_checked", False),
                }
            }
        }
        
        # Convert nested objects to serializable dicts
        if hasattr(extracted["intent"], "model_dump"):
            extracted["intent"] = extracted["intent"].model_dump()
        elif hasattr(extracted["intent"], "dict"):
            extracted["intent"] = extracted["intent"].dict()
            
        logger.info({
            "event": "workflow_data_extracted",
            "conversation_id": extracted["conversation_id"],
            "agent_reply_length": len(extracted["agent_reply"]),
            "actions_count": len(extracted["agent_actions"]),
            "format_version": "structured"
        })
        
        return extracted
    
    @staticmethod
    def validate_structured_format(response: Dict[str, Any]) -> bool:
        """Validate response against MVP spec"""
        
        # Validate required field
        if "reply" not in response or not isinstance(response["reply"], str):
            logger.error({
                "event": "chat_response_validation_failed",
                "issue": "missing_or_invalid_reply",
                "response_keys": list(response.keys())
            })
            return False
        
        # Validate optional field if present
        if "actions" in response:
            if not isinstance(response["actions"], list):
                logger.error({
                    "event": "chat_response_validation_failed",
                    "issue": "actions_not_a_list",
                    "actions_type": type(response["actions"])
                })
                return False
            
            for i, action in enumerate(response["actions"]):
                if not isinstance(action, str):
                    logger.error({
                        "event": "chat_response_validation_failed",
                        "issue": "action_not_string",
                        "action_index": i,
                        "action_type": type(action)
                    })
                    return False
        
        logger.info({
            "event": "chat_response_validation_success",
            "conversation_id": response.get("conversation_id", "unknown"),
            "actions_count": len(response.get("actions", [])),
            "format_valid": True
        })
        
        return True
    
    @staticmethod
    def create_json_response(data: Dict[str, Any], format_version: str, status_code: int = 200) -> JSONResponse:
        """Create appropriate JSON response with format-specific handling"""
        
        if format_version == "structured":
            # Validate structured format before returning
            if not ChatResponseBuilder.validate_structured_format(data):
                # Fallback to minimal valid structured format
                fallback_data = {
                    "reply": data.get("reply", ""),
                    "actions": None
                }
                return JSONResponse(fallback_data, status_code=status_code)
            
            return JSONResponse(data, status_code=status_code)
        else:
            # Full format: minimal validation (already comprehensive)
            return JSONResponse(data, status_code=status_code)


# Export commonly used classes and functions
__all__ = [
    "ChatResponseBuilder",
    "StructuredChatResponse",
    "FullChatResponse"
]