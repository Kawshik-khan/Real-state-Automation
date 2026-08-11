"""Re-export lean models for backward compatibility."""
from app.models.models import (
    Base,
    UserRecord,
    ConversationRecord,
    MessageRecord,
    ProjectRecord,
    KnowledgeDocumentRecord,
    ChunkRecord,
    MediaRecord,
    AnalyticsRecord,
    LogRecord,
)

# Compatibility aliases
CustomerRecord = UserRecord
AuditRecord = LogRecord
