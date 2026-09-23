"""Test LangSmith connectivity and trace an agent execution."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# 1. Load backend/.env
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)

print("=" * 60)
print("  GLG Assets — LangSmith Tracing & Observability Verification")
print("=" * 60)
print(f"Loaded .env from: {env_path}")
print(f"LANGSMITH_TRACING  = {os.getenv('LANGSMITH_TRACING')}")
print(f"LANGSMITH_ENDPOINT = {os.getenv('LANGSMITH_ENDPOINT')}")
print(f"LANGSMITH_PROJECT  = {os.getenv('LANGSMITH_PROJECT')}")
api_key = os.getenv("LANGSMITH_API_KEY", "")
if api_key:
    masked_key = api_key[:10] + "..." + api_key[-4:]
    print(f"LANGSMITH_API_KEY  = {masked_key} (Valid length: {len(api_key)})")
else:
    print("ERROR: LANGSMITH_API_KEY is not set in backend/.env!")
    sys.exit(1)

# 2. Test LangSmith Client Auth
print("\n[Step 1] Verifying LangSmith Client Authentication...")
try:
    from langsmith import Client
    client = Client()
    project_name = os.getenv("LANGSMITH_PROJECT", "glg-assets-ai-os")
    
    # Check or create project
    try:
        project = client.read_project(project_name=project_name)
        print(f" -> Project '{project_name}' exists (ID: {project.id})")
    except Exception:
        project = client.create_project(project_name=project_name, description="GLG Assets Social AI OS Multi-Agent Graph Traces")
        print(f" -> Project '{project_name}' created successfully (ID: {project.id})")

    print(" -> Authentication with LangSmith API: SUCCESS!")
except Exception as e:
    print(f" -> LangSmith Client Error: {e}")
    sys.exit(1)

# 3. Test Graph Tracing with real LangGraph execution
print("\n[Step 2] Executing test message through LangGraph AI pipeline...")
try:
    from app.agents.graph import ai_graph
    from app.agents.state import AIState

    async def run_trace():
        initial_state = AIState(
            message="Hello! What luxury 3BHK flats are available in Banani or Gulshan?",
            conversation_id="conv_langsmith_test_001",
            user_id="test_langsmith_tester",
            session_id="session_langsmith_verify_001",
        )
        result = await ai_graph.ainvoke(initial_state)
        return result

    result = asyncio.run(run_trace())
    print(" -> LangGraph execution finished successfully!")
    supervisor_res = result.get("supervisor")
    intent = supervisor_res.intent if hasattr(supervisor_res, "intent") else (supervisor_res.get("intent") if isinstance(supervisor_res, dict) else "N/A")
    print(f" -> Identified Intent: {intent}")
    reply = result.get("final_response") or result.get("reply") or result.get("message")
    if reply:
        preview = (reply[:100] + "...") if len(reply) > 100 else reply
        print(f" -> Agent Reply Preview: {preview}")

    print("\n[Step 3] Verification Complete!")
    print(f"Trace has been transmitted to LangSmith project: '{project_name}'")
    print("Open your LangSmith dashboard to inspect the interactive execution graph:")
    print("https://smith.langchain.com")
except Exception as e:
    print(f" -> Error during LangGraph execution: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
