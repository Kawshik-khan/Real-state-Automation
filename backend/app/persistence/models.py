"""Re-export lean models for backward compatibility."""
from app.models.models import (
    LogRecord,
    UserRecord,
)

# Compatibility aliases
CustomerRecord = UserRecord
AuditRecord = LogRecord
