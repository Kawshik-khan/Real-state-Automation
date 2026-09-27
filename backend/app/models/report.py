"""Pydantic schemas and enums for Scheduled Report Generation and Delivery."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReportFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReportType(str, Enum):
    DAILY_DIGEST = "daily_digest"
    WEEKLY_CROSS_ROLE = "weekly_cross_role"
    MONTHLY_AUDIT = "monthly_audit"


class DeliveryChannel(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    IN_APP = "in_app"


class DeliveryStatus(str, Enum):
    GENERATED = "generated"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    PARTIALLY_DELIVERED = "partially_delivered"
    FAILED = "failed"


class ReportRecipientSchema(BaseModel):
    id: Optional[str] = None
    role: str = Field(..., description="Target role: admin, manager, etc.")
    name: str = Field(..., description="Recipient full name")
    email: Optional[str] = Field(None, description="Email address for HTML reports")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram Chat ID for alerts")
    whatsapp_phone: Optional[str] = Field(None, description="WhatsApp phone number with country code")
    channels: List[DeliveryChannel] = Field(
        default_factory=lambda: [DeliveryChannel.EMAIL, DeliveryChannel.TELEGRAM, DeliveryChannel.WHATSAPP],
        description="Active delivery channels for this recipient",
    )
    is_active: bool = True


class ReportScheduleBase(BaseModel):
    name: str = Field(..., description="Human-readable schedule name")
    report_type: ReportType = ReportType.DAILY_DIGEST
    frequency: ReportFrequency = ReportFrequency.DAILY
    execution_hour_utc: int = Field(8, ge=0, le=23, description="Hour of day (0-23 UTC)")
    execution_day_of_week: int = Field(0, ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    is_active: bool = True
    recipients: List[ReportRecipientSchema] = Field(default_factory=list)
    channels: List[DeliveryChannel] = Field(
        default_factory=lambda: [DeliveryChannel.EMAIL, DeliveryChannel.TELEGRAM, DeliveryChannel.WHATSAPP, DeliveryChannel.IN_APP]
    )
    tenant_id: str = "glg-assets"


class ReportScheduleCreate(ReportScheduleBase):
    pass


class ReportScheduleUpdate(BaseModel):
    name: Optional[str] = None
    report_type: Optional[ReportType] = None
    frequency: Optional[ReportFrequency] = None
    execution_hour_utc: Optional[int] = Field(None, ge=0, le=23)
    execution_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    is_active: Optional[bool] = None
    recipients: Optional[List[ReportRecipientSchema]] = None
    channels: Optional[List[DeliveryChannel]] = None


class ReportScheduleResponse(ReportScheduleBase):
    id: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReportDeliveryLogSchema(BaseModel):
    recipient_name: str
    recipient_role: str
    channel: str
    target: str
    status: str  # sent, failed, simulated
    details: Optional[str] = None
    delivered_at: str


class GeneratedReportResponse(BaseModel):
    id: str
    schedule_id: Optional[str] = None
    title: str
    report_type: str
    period_start: str
    period_end: str
    metrics_data: Dict[str, Any] = Field(default_factory=dict)
    executive_summary: str
    html_content: Optional[str] = None
    whatsapp_content: Optional[str] = None
    telegram_content: Optional[str] = None
    delivery_status: DeliveryStatus
    delivery_details: List[ReportDeliveryLogSchema] = Field(default_factory=list)
    triggered_by: str = "scheduled_worker"
    created_at: str


class ReportTriggerRequest(BaseModel):
    target_recipients: Optional[List[ReportRecipientSchema]] = None
    channels_override: Optional[List[DeliveryChannel]] = None
    period_days: Optional[int] = 1


class TestDispatchRequest(BaseModel):
    recipient_name: str = "Admin Test User"
    email: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    whatsapp_phone: Optional[str] = None
    report_type: ReportType = ReportType.DAILY_DIGEST
