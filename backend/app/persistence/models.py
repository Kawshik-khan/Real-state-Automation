"""Re-export lean models for backward compatibility."""
from app.models.models import (
    Base,
    LogRecord,
    UserRecord,
)

# Compatibility aliases
CustomerRecord = UserRecord
AuditRecord = LogRecord

__all__ = [
    "Base",
    "CustomerRecord",
    "AuditRecord",
    "LogRecord",
    "UserRecord",
]
