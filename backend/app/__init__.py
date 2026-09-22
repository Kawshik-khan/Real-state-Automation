"""GLG Assets Social AI OS — Backend Application Package."""
import warnings

# Suppress known LangGraph/LangChain internal serializer deprecation warnings on startup
warnings.filterwarnings(
    "ignore",
    category=PendingDeprecationWarning,
    message=r".*allowed_objects.*",
)
warnings.filterwarnings(
    "ignore",
    message=r".*allowed_objects.*",
)
