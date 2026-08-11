"""n8n integration adapter for workflow automation."""
import hashlib
import hmac
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from pydantic import BaseModel, Field, HttpUrl, validator

from app.config import settings


class N8nWebhookEvent(BaseModel):
    """Event received from n8n webhook."""
    
    event_type: str = Field(..., description="Type of the event")
    event_id: str = Field(..., description="Unique event identifier")
    occurred_at: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    signature: Optional[str] = Field(None, description="HMAC signature for verification")


class N8nWorkflowTrigger(BaseModel):
    """Trigger to execute an n8n workflow."""
    
    workflow_id: str = Field(..., description="n8n workflow ID")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for workflow")
    options: Dict[str, Any] = Field(default_factory=dict, description="Workflow execution options")


class N8nWorkflowExecution(BaseModel):
    """Result of n8n workflow execution."""
    
    execution_id: str = Field(..., description="Execution ID")
    status: str = Field(..., description="Execution status")
    result: Dict[str, Any] = Field(default_factory=dict, description="Execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: datetime = Field(..., description="Execution start time")
    finished_at: Optional[datetime] = Field(None, description="Execution finish time")


class N8nConfig(BaseModel):
    """Configuration for n8n integration."""
    
    webhook_url: HttpUrl = Field(..., description="n8n webhook URL")
    api_url: HttpUrl = Field(..., description="n8n API URL")
    api_key: str = Field(..., description="n8n API key")
    webhook_secret: str = Field(..., description="Secret for webhook signature verification")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    @validator('api_url')
    def validate_api_url(cls, v: HttpUrl) -> HttpUrl:
        """Ensure API URL ends with /api/v1."""
        if not str(v).endswith('/api/v1'):
            return HttpUrl(str(v) + '/api/v1')
        return v


class N8nClient:
    """Client for interacting with n8n API and webhooks."""
    
    def __init__(self, config: N8nConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self._client
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature using HMAC-SHA256."""
        expected_signature = hmac.new(
            self.config.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)
    
    async def trigger_workflow(
        self,
        trigger: N8nWorkflowTrigger
    ) -> N8nWorkflowExecution:
        """Trigger an n8n workflow execution."""
        url = f"{self.config.api_url}/workflows/{trigger.workflow_id}/execute"
        
        response = await self.client.post(
            url,
            json={
                "data": trigger.input_data,
                "options": trigger.options
            }
        )
        response.raise_for_status()
        
        data = response.json()
        return N8nWorkflowExecution(
            execution_id=data["executionId"],
            status=data["status"],
            result=data.get("data", {}),
            error=data.get("error"),
            started_at=datetime.fromisoformat(data["startedAt"]),
            finished_at=datetime.fromisoformat(data["finishedAt"]) if data.get("finishedAt") else None
        )
    
    async def get_workflow_execution(
        self,
        execution_id: str
    ) -> N8nWorkflowExecution:
        """Get workflow execution status."""
        url = f"{self.config.api_url}/executions/{execution_id}"
        
        response = await self.client.get(url)
        response.raise_for_status()
        
        data = response.json()
        return N8nWorkflowExecution(
            execution_id=data["id"],
            status=data["status"],
            result=data.get("data", {}),
            error=data.get("error"),
            started_at=datetime.fromisoformat(data["startedAt"]),
            finished_at=datetime.fromisoformat(data["finishedAt"]) if data.get("finishedAt") else None
        )
    
    async def send_webhook(
        self,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send event to n8n webhook."""
        payload = {
            "event_type": event_type,
            "event_id": str(UUID()),
            "occurred_at": datetime.utcnow().isoformat(),
            "data": data,
            "metadata": metadata or {}
        }
        
        try:
            response = await self.client.post(
                str(self.config.webhook_url),
                json=payload
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False


class N8nEventPublisher:
    """Service for publishing events to n8n."""
    
    def __init__(self, client: N8nClient):
        self.client = client
    
    async def publish_lead_created(
        self,
        lead_id: UUID,
        customer_id: UUID,
        source: str,
        initial_intent: str,
        budget: Optional[float] = None,
        preferred_location: Optional[str] = None,
        timeline: Optional[str] = None
    ) -> bool:
        """Publish LeadCreated event."""
        return await self.client.send_webhook(
            "LeadCreated",
            {
                "lead_id": str(lead_id),
                "customer_id": str(customer_id),
                "source": source,
                "initial_intent": initial_intent,
                "budget": budget,
                "preferred_location": preferred_location,
                "timeline": timeline
            },
            {
                "priority": "high",
                "retry_policy": "3_attempts_1h_ttl"
            }
        )
    
    async def publish_conversation_started(
        self,
        conversation_id: UUID,
        user_id: UUID,
        channel: str,
        initial_message: str
    ) -> bool:
        """Publish ConversationStarted event."""
        return await self.client.send_webhook(
            "ConversationStarted",
            {
                "conversation_id": str(conversation_id),
                "user_id": str(user_id),
                "channel": channel,
                "initial_message": initial_message
            },
            {
                "priority": "high",
                "retry_policy": "3_attempts_1h_ttl"
            }
        )
    
    async def publish_booking_created(
        self,
        booking_id: UUID,
        customer_id: UUID,
        property_id: UUID,
        date: str,
        time: str
    ) -> bool:
        """Publish BookingCreated event."""
        return await self.client.send_webhook(
            "BookingCreated",
            {
                "booking_id": str(booking_id),
                "customer_id": str(customer_id),
                "property_id": str(property_id),
                "date": date,
                "time": time
            },
            {
                "priority": "high",
                "retry_policy": "3_attempts_1h_ttl"
            }
        )
    
    async def publish_payment_completed(
        self,
        payment_id: UUID,
        booking_id: UUID,
        customer_id: UUID,
        amount: float,
        currency: str,
        payment_method: str,
        transaction_id: str
    ) -> bool:
        """Publish PaymentCompleted event."""
        return await self.client.send_webhook(
            "PaymentCompleted",
            {
                "payment_id": str(payment_id),
                "booking_id": str(booking_id),
                "customer_id": str(customer_id),
                "amount": amount,
                "currency": currency,
                "payment_method": payment_method,
                "transaction_id": transaction_id
            },
            {
                "priority": "critical",
                "retry_policy": "5_attempts_24h_ttl"
            }
        )
    
    async def publish_human_handoff(
        self,
        conversation_id: UUID,
        user_id: UUID,
        reason: str,
        summary: str,
        target_agent_id: Optional[str] = None
    ) -> bool:
        """Publish HumanHandoff event."""
        return await self.client.send_webhook(
            "HumanHandoff",
            {
                "conversation_id": str(conversation_id),
                "user_id": str(user_id),
                "reason": reason,
                "summary": summary,
                "target_agent_id": target_agent_id
            },
            {
                "priority": "critical",
                "retry_policy": "5_attempts_24h_ttl"
            }
        )
