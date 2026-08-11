"""n8n webhook and workflow execution endpoints."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.adapters.n8n import (
    N8nClient,
    N8nConfig,
    N8nEventPublisher,
    N8nWebhookEvent,
    N8nWorkflowExecution,
    N8nWorkflowTrigger,
)


class WebhookResponse(BaseModel):
    """Response for webhook endpoint."""
    success: bool = True
    message: str = "Event received"


class WorkflowExecutionResponse(BaseModel):
    """Response for workflow execution."""
    execution_id: str
    status: str
    result: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None


def build_n8n_router(config: N8nConfig) -> APIRouter:
    """Build n8n integration router."""
    router = APIRouter(prefix="/api/v1/n8n", tags=["n8n"])
    client = N8nClient(config)
    publisher = N8nEventPublisher(client)
    
    @router.post("/webhook", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
    async def receive_webhook(
        request: Request,
        x_webhook_signature: Optional[str] = Header(default=None, alias="X-Webhook-Signature")
    ) -> WebhookResponse:
        """Receive events from n8n webhook."""
        body = await request.body()
        
        # Verify signature if provided
        if x_webhook_signature:
            if not client.verify_webhook_signature(body, x_webhook_signature):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        
        try:
            event_data = await request.json()
            event = N8nWebhookEvent(**event_data)
            
            # Process event based on type
            await _process_event(event, publisher)
            
            return WebhookResponse(success=True, message="Event processed")
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event data: {str(e)}"
            )
    
    @router.post("/workflows/trigger", response_model=WorkflowExecutionResponse, status_code=status.HTTP_201_CREATED)
    async def trigger_workflow(
        trigger: N8nWorkflowTrigger,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
    ) -> WorkflowExecutionResponse:
        """Trigger an n8n workflow execution."""
        # Verify API key if configured
        if x_api_key and x_api_key != config.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        try:
            execution = await client.trigger_workflow(trigger)
            
            return WorkflowExecutionResponse(
                execution_id=execution.execution_id,
                status=execution.status,
                result=execution.result
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to trigger workflow: {str(e)}"
            )
    
    @router.get("/workflows/executions/{execution_id}", response_model=N8nWorkflowExecution)
    async def get_workflow_execution(
        execution_id: str,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
    ) -> N8nWorkflowExecution:
        """Get workflow execution status."""
        # Verify API key if configured
        if x_api_key and x_api_key != config.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        try:
            return await client.get_workflow_execution(execution_id)
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get execution: {str(e)}"
            )
    
    @router.post("/events/lead-created", response_model=WebhookResponse)
    async def publish_lead_created(
        lead_id: str,
        customer_id: str,
        source: str,
        initial_intent: str,
        budget: Optional[float] = None,
        preferred_location: Optional[str] = None,
        timeline: Optional[str] = None
    ) -> WebhookResponse:
        """Publish LeadCreated event to n8n."""
        from uuid import UUID
        
        success = await publisher.publish_lead_created(
            lead_id=UUID(lead_id),
            customer_id=UUID(customer_id),
            source=source,
            initial_intent=initial_intent,
            budget=budget,
            preferred_location=preferred_location,
            timeline=timeline
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish event"
            )
        
        return WebhookResponse(success=True, message="Event published")
    
    @router.post("/events/conversation-started", response_model=WebhookResponse)
    async def publish_conversation_started(
        conversation_id: str,
        user_id: str,
        channel: str,
        initial_message: str
    ) -> WebhookResponse:
        """Publish ConversationStarted event to n8n."""
        from uuid import UUID
        
        success = await publisher.publish_conversation_started(
            conversation_id=UUID(conversation_id),
            user_id=UUID(user_id),
            channel=channel,
            initial_message=initial_message
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish event"
            )
        
        return WebhookResponse(success=True, message="Event published")
    
    @router.post("/events/booking-created", response_model=WebhookResponse)
    async def publish_booking_created(
        booking_id: str,
        customer_id: str,
        property_id: str,
        date: str,
        time: str
    ) -> WebhookResponse:
        """Publish BookingCreated event to n8n."""
        from uuid import UUID
        
        success = await publisher.publish_booking_created(
            booking_id=UUID(booking_id),
            customer_id=UUID(customer_id),
            property_id=UUID(property_id),
            date=date,
            time=time
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish event"
            )
        
        return WebhookResponse(success=True, message="Event published")
    
    @router.post("/events/payment-completed", response_model=WebhookResponse)
    async def publish_payment_completed(
        payment_id: str,
        booking_id: str,
        customer_id: str,
        amount: float,
        currency: str,
        payment_method: str,
        transaction_id: str
    ) -> WebhookResponse:
        """Publish PaymentCompleted event to n8n."""
        from uuid import UUID
        
        success = await publisher.publish_payment_completed(
            payment_id=UUID(payment_id),
            booking_id=UUID(booking_id),
            customer_id=UUID(customer_id),
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            transaction_id=transaction_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish event"
            )
        
        return WebhookResponse(success=True, message="Event published")
    
    @router.post("/events/human-handoff", response_model=WebhookResponse)
    async def publish_human_handoff(
        conversation_id: str,
        user_id: str,
        reason: str,
        summary: str,
        target_agent_id: Optional[str] = None
    ) -> WebhookResponse:
        """Publish HumanHandoff event to n8n."""
        from uuid import UUID
        
        success = await publisher.publish_human_handoff(
            conversation_id=UUID(conversation_id),
            user_id=UUID(user_id),
            reason=reason,
            summary=summary,
            target_agent_id=target_agent_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish event"
            )
        
        return WebhookResponse(success=True, message="Event published")
    
    return router


async def _process_event(event: N8nWebhookEvent, publisher: N8nEventPublisher):
    """Process incoming event from n8n."""
    # This would handle events sent back from n8n workflows
    # For example, workflow completion notifications, approval responses, etc.
    
    if event.event_type == "WorkflowCompleted":
        # Handle workflow completion
        pass
    elif event.event_type == "ApprovalGranted":
        # Handle approval granted
        pass
    elif event.event_type == "ApprovalDenied":
        # Handle approval denied
        pass
    # Add more event types as needed
