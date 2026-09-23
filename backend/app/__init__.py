"""GLG Assets Social AI OS — Backend Application Package."""
import warnings

# Suppress known LangGraph/LangChain internal serializer deprecation warnings on startup
warnings.filterwarnings("ignore", message="The default value of ")
warnings.filterwarnings("ignore", message=r".*allowed_objects.*")
warnings.filterwarnings("ignore", category=UserWarning, module=r".*langgraph.*")
warnings.filterwarnings("ignore", category=UserWarning, module=r".*langchain.*")
