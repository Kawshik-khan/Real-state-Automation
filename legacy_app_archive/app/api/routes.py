from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.application.ai import AIOrchestrator
from app.adapters.runtime import InMemoryIdempotencyStore
from app.application.services import ConversationClosed, ConversationNotFound, ConversationService
from app.domain.models import Conversation, Message


class CreateConversationRequest(BaseModel):
    tenant_id: UUID
    customer_id: UUID | None = None
    channel: str = Field(min_length=1, max_length=40)


class SendMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)


class AssistantResponse(BaseModel):
    message: Message
    run_id: UUID
    intent: str
    confidence: float
    fallback: bool


def build_router(
    service: ConversationService,
    orchestrator: AIOrchestrator,
    idempotency: InMemoryIdempotencyStore | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    idempotency = idempotency or InMemoryIdempotencyStore()

    @router.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED)
    def create_conversation(
        request: CreateConversationRequest,
        correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
        tenant_header: UUID | None = Header(default=None, alias="X-Tenant-Id"),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> Conversation:
        if tenant_header is not None and tenant_header != request.tenant_id:
            raise HTTPException(status_code=403, detail="TENANT_SCOPE_VIOLATION")
        if idempotency_key and not idempotency.claim(str(request.tenant_id), idempotency_key):
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_KEY_REUSED")
        return service.create(Conversation(**request.model_dump()))

    @router.get("/conversations/{conversation_id}", response_model=Conversation)
    def get_conversation(
        conversation_id: UUID,
        tenant_header: UUID | None = Header(default=None, alias="X-Tenant-Id"),
    ) -> Conversation:
        conversation = service.repository.get(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="CONVERSATION_NOT_FOUND")
        if tenant_header is not None and tenant_header != conversation.tenant_id:
            raise HTTPException(status_code=404, detail="CONVERSATION_NOT_FOUND")
        return conversation

    @router.post("/conversations/{conversation_id}/messages", response_model=AssistantResponse, status_code=status.HTTP_201_CREATED)
    def receive_message(
        conversation_id: UUID,
        request: SendMessageRequest,
        correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    ) -> AssistantResponse:
        try:
            inbound = service.receive_message(conversation_id, request.text)
            conversation = service.repository.get(conversation_id)
            if conversation is None:
                raise ConversationNotFound
            assistant, result = orchestrator.respond(conversation, inbound, correlation_id)
            service.append_outbound(conversation_id, assistant)
            return AssistantResponse(
                message=assistant,
                run_id=result.run_id,
                intent=result.intent,
                confidence=result.confidence,
                fallback=result.fallback,
            )
        except ConversationNotFound as exc:
            raise HTTPException(status_code=404, detail="CONVERSATION_NOT_FOUND") from exc
        except ConversationClosed as exc:
            raise HTTPException(status_code=409, detail="CONVERSATION_CLOSED") from exc

    @router.post("/conversations/{conversation_id}/close", response_model=Conversation)
    def close_conversation(conversation_id: UUID) -> Conversation:
        try:
            return service.close(conversation_id)
        except ConversationNotFound as exc:
            raise HTTPException(status_code=404, detail="CONVERSATION_NOT_FOUND") from exc

    return router
