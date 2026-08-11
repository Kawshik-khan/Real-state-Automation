"""Projects API — GET /api/projects and GET /api/project/{id}."""

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_automation_secret as _auth
from app.agents.property_agent import property_agent

router = APIRouter()


@router.get("/projects", summary="List all real-estate projects")
async def list_projects(auth: dict = Depends(_auth)):
    """Return all available projects with their inventory units."""
    projects = await property_agent.get_projects()
    return {
        "success": True,
        "projects": projects,
        "count": len(projects),
        "tenantId": auth["tenant_id"],
    }


@router.get("/project/{project_id}", summary="Get a single project by ID or name")
async def get_project(project_id: str, auth: dict = Depends(_auth)):
    """Return details for a specific project. The project_id can be a name (case-insensitive partial match)."""
    projects = await property_agent.get_projects()
    pid_lower = project_id.lower()

    # Try exact match first, then partial match
    for proj in projects:
        if proj["name"].lower() == pid_lower:
            return {"success": True, "project": proj, "tenantId": auth["tenant_id"]}

    for proj in projects:
        if pid_lower in proj["name"].lower() or pid_lower in proj["location"].lower():
            return {"success": True, "project": proj, "tenantId": auth["tenant_id"]}

    raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
