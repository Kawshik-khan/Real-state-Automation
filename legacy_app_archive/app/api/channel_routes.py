from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.channels import ChannelAdapter, CanonicalInboundMessage


class ChannelWebhookRequest(BaseModel):
    message_id: str = Field(min_length=1, max_length=200)
    sender: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=10_000)


def build_channel_router(adapter: ChannelAdapter) -> APIRouter:
    router = APIRouter(prefix="/api/v1/webhooks", tags=["channels"])

    @router.post("/{channel}", response_model=CanonicalInboundMessage)
    def receive_webhook(channel: str, request: ChannelWebhookRequest, tenant_id: UUID = Header(..., alias="X-Tenant-Id"), signature: str | None = Header(default=None, alias="X-Webhook-Signature")) -> CanonicalInboundMessage:
        if not signature:
            raise HTTPException(status_code=401, detail="WEBHOOK_SIGNATURE_REQUIRED")
        try:
            message = adapter.normalize(channel, tenant_id, request.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="INVALID_CHANNEL_MESSAGE") from exc
        if message is None:
            raise HTTPException(status_code=200, detail="DUPLICATE_WEBHOOK")
        return message

    return router