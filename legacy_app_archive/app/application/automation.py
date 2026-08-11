"""Automation service for n8n workflow integration."""
from typing import Optional
from uuid import UUID

from app.adapters.n8n import N8nClient, N8nConfig, N8nEventPublisher
from app.config import settings


class AutomationService:
    """Service for integrating with n8n automation workflows."""
    
    def __init__(self):
        self._client: Optional[N8nClient] = None
        self._publisher: Optional[N8nEventPublisher] = None
        self._enabled = settings.enable_n8n
    
    @property
    def client(self) -> Optional[N8nClient]:
        """Get or create n8n client."""
        if not self._enabled:
            return None
        
        if self._client is None:
            config = N8nConfig(
                webhook_url=settings.n8n_webhook_url,
                api_url=settings.n8n_api_url,
                api_key=settings.n8n_api_key,
                webhook_secret=settings.n8n_webhook_secret,
                timeout=settings.n8n_timeout
            )
            self._client = N8nClient(config)
            self._publisher = N8nEventPublisher(self._client)
        
        return self._client
    
    @property
    def publisher(self) -> Optional[N8nEventPublisher]:
        """Get event publisher."""
        return self._publisher
    
    async def publish_lead_created(
        self,
        lead_id: UUID,
        customer_id: UUID,
        source: str,
        initial_intent: str,
        budget: Optional[float] = None,
        preferred_location: Optional[str] = None,
        timeline: Optional[str] = None,
        tenant_id: Optional[UUID] = None
    ) -> bool:
        """Publish LeadCreated event to n8n."""
        if not self._enabled or not self.publisher:
            return False
        
        return await self.publisher.publish_lead_created(
            lead_id=lead_id,
            customer_id=customer_id,
            source=source,
            initial_intent=initial_intent,
            budget=budget,
            preferred_location=preferred_location,
            timeline=timeline
        )
    
    async def publish_conversation_started(
        self,
        conversation_id: UUID,
        user_id: UUID,
        channel: str,
        initial_message: str
    ) -> bool:
        """Publish ConversationStarted event to n8n."""
        if not self._enabled or not self.publisher:
            return False
        
        return await self.publisher.publish_conversation_started(
            conversation_id=conversation_id,
            user_id=user_id,
            channel=channel,
            initial_message=initial_message
        )
    
    async def publish_booking_created(
        self,
        booking_id: UUID,
        customer_id: UUID,
        property_id: UUID,
        date: str,
        time: str,
        tenant_id: Optional[UUID] = None
    ) -> bool:
        """Publish BookingCreated event to n8n."""
        if not self._enabled or not self.publisher:
            return False
        
        return await self.publisher.publish_booking_created(
            booking_id=booking_id,
            customer_id=customer_id,
            property_id=property_id,
            date=date,
            time=time
        )
    
    async def publish_payment_completed(
        self,
        payment_id: UUID,
        booking_id: UUID,
        customer_id: UUID,
        amount: float,
        currency: str,
        payment_method: str,
        transaction_id: str,
        tenant_id: Optional[UUID] = None
    ) -> bool:
        """Publish PaymentCompleted event to n8n."""
        if not self._enabled or not self.publisher:
            return False
        
        return await self.publisher.publish_payment_completed(
            payment_id=payment_id,
            booking_id=booking_id,
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            transaction_id=transaction_id
        )
    
    async def publish_human_handoff(
        self,
        conversation_id: UUID,
        user_id: UUID,
        reason: str,
        summary: str,
        target_agent_id: Optional[str] = None
    ) -> bool:
        """Publish HumanHandoff event to n8n."""
        if not self._enabled or not self.publisher:
            return False
        
        return await self.publisher.publish_human_handoff(
            conversation_id=conversation_id,
            user_id=user_id,
            reason=reason,
            summary=summary,
            target_agent_id=target_agent_id
        )
    
    async def publish_social_media_post(
        self,
        content: str,
        platforms: list,
        media_urls: Optional[list] = None,
        scheduled_for: Optional[str] = None,
        campaign_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """Publish SocialMediaPost event to n8n."""
        if not self._enabled or not self.publisher:
            return False
        
        return await self.client.send_webhook(
            "SocialMediaPost",
            {
                "content": content,
                "platforms": platforms,
                "media_urls": media_urls or [],
                "scheduled_for": scheduled_for,
                "campaign_id": campaign_id,
                "metadata": metadata or {}
            },
            {
                "priority": "medium",
                "retry_policy": "2_attempts_30min_ttl"
            }
        )
    
    async def publish_content_distribution(
        self,
        content_id: str,
        title: str,
        body: str,
        channels: list,
        media: Optional[list] = None,
        tags: Optional[list] = None,
        category: Optional[str] = None,
        schedule: Optional[str] = None
    ) -> bool:
        """Publish ContentDistribution event to n8n."""
        if not self._enabled or not self.publisher:
            return False
        
        return await self.client.send_webhook(
            "ContentDistribution",
            {
                "content_id": content_id,
                "title": title,
                "body": body,
                "channels": channels,
                "media": media or [],
                "tags": tags or [],
                "category": category or "general",
                "schedule": schedule or "immediate"
            },
            {
                "priority": "medium",
                "retry_policy": "2_attempts_30min_ttl"
            }
        )
    
    async def publish_campaign_execution(
        self,
        campaign_id: str,
        name: str,
        content_pieces: list,
        platforms: list,
        start_date: str,
        end_date: str,
        target_audience: Optional[list] = None,
        budget: Optional[float] = None
    ) -> bool:
        """Publish CampaignExecution event to n8n."""
        if not self._enabled or not self.publisher:
            return False
        
        return await self.client.send_webhook(
            "CampaignExecution",
            {
                "campaign_id": campaign_id,
                "name": name,
                "content_pieces": content_pieces,
                "platforms": platforms,
                "start_date": start_date,
                "end_date": end_date,
                "target_audience": target_audience or [],
                "budget": budget or 0
            },
            {
                "priority": "high",
                "retry_policy": "3_attempts_1h_ttl"
            }
        )
    
    async def close(self):
        """Close n8n client."""
        if self._client:
            await self._client.close()
            self._client = None
            self._publisher = None


# Global automation service instance
automation_service = AutomationService()
