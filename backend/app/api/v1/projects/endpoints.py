"""Projects API — GET /api/projects, GET /api/project/{id}, and POST /api/projects.

Backed by Supabase/PostgreSQL ProjectRecord with in-memory fallback.
"""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.property_agent import property_agent
from app.database import get_session
from app.dependencies import require_automation_secret as _auth
from app.models.models import ProjectRecord

router = APIRouter()


def _format_db_project(proj: ProjectRecord) -> dict:
    """Format SQLAlchemy ProjectRecord into frontend-ready dict."""
    features = proj.features or {}
    return {
        "id": proj.project_id,
        "name": proj.name,
        "location": proj.location,
        "price": proj.price,
        "price_short": features.get("price_short", proj.price.split("-")[0].strip() if "-" in proj.price else proj.price),
        "price_val": proj.price_val or 0,
        "bedrooms": f"{proj.bedrooms} BHK" if proj.bedrooms else "2 & 3 BHK",
        "description": proj.description or "",
        "lat": features.get("lat", 23.7925),
        "lng": features.get("lng", 90.4078),
        "status": features.get("status", "Available"),
        "valuation": features.get("valuation", "৳10.0 Cr"),
        "units_available": features.get("units_available", 4),
        "total_units": features.get("total_units", 12),
        "image": (features.get("images", ["https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=600&q=80"]))[0],
        "images": features.get("images", []),
        "amenities": features.get("amenities", ["24/7 Security", "Backup Generator", "Lift"]),
        "proximity": features.get("proximity", [
            {"name": "Central Park", "dist": "0.5 km"},
            {"name": "Hospital", "dist": "1.2 km"}
        ]),
        "brochure_url": features.get("brochure_url", ""),
    }


@router.get("/projects", summary="List all real-estate projects")
async def list_projects(
    db: AsyncSession = Depends(get_session),
    auth: dict = Depends(_auth)
):
    """Return all available projects from Supabase PostgreSQL, with fallback."""
    try:
        stmt = select(ProjectRecord).order_by(ProjectRecord.created_at.desc())
        res = await db.execute(stmt)
        records = res.scalars().all()
        if records:
            formatted = [_format_db_project(p) for p in records]
            return {
                "success": True,
                "projects": formatted,
                "count": len(formatted),
                "source": "database",
                "tenantId": auth["tenant_id"],
            }
    except Exception:
        pass

    # Fallback to canonical repository
    projects = await property_agent.get_projects()
    return {
        "success": True,
        "projects": projects,
        "count": len(projects),
        "source": "canonical_fallback",
        "tenantId": auth["tenant_id"],
    }


@router.get("/project/{project_id}", summary="Get a single project by ID or name")
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_session),
    auth: dict = Depends(_auth)
):
    """Return details for a specific project. The project_id can be a name (case-insensitive partial match)."""
    pid_lower = project_id.lower()

    try:
        stmt = select(ProjectRecord)
        res = await db.execute(stmt)
        records = res.scalars().all()
        for p in records:
            if p.project_id.lower() == pid_lower or p.name.lower() == pid_lower or pid_lower in p.name.lower():
                return {"success": True, "project": _format_db_project(p), "tenantId": auth["tenant_id"]}
    except Exception:
        pass

    # Fallback check
    projects = await property_agent.get_projects()
    for proj in projects:
        if proj["name"].lower() == pid_lower or proj.get("id", "").lower() == pid_lower:
            return {"success": True, "project": proj, "tenantId": auth["tenant_id"]}

    for proj in projects:
        if pid_lower in proj["name"].lower() or pid_lower in proj["location"].lower():
            return {"success": True, "project": proj, "tenantId": auth["tenant_id"]}

    raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")


@router.post("/projects", summary="Create a new real-estate project development")
async def create_project(
    body: dict,
    db: AsyncSession = Depends(get_session),
    auth: dict = Depends(_auth)
):
    """Create a new property listing and save to database."""
    name = body.get("name")
    location = body.get("location")
    price = body.get("price", "৳1.0 Crore")
    if not name or not location:
        raise HTTPException(status_code=400, detail="Name and location are required")

    project_id = body.get("project_id") or f"proj_{uuid4().hex[:8]}"
    bedrooms = body.get("bedrooms", 3)
    if isinstance(bedrooms, str):
        digits = "".join(c for c in bedrooms if c.isdigit())
        bedrooms = int(digits) if digits else 3

    features = {
        "lat": float(body.get("lat", 23.7925)),
        "lng": float(body.get("lng", 90.4078)),
        "status": body.get("status", "Available"),
        "price_short": body.get("price_short", price.split("-")[0].strip() if "-" in price else price),
        "valuation": body.get("valuation", "৳10.0 Cr"),
        "units_available": int(body.get("units_available", 4)),
        "total_units": int(body.get("total_units", 12)),
        "amenities": body.get("amenities", ["24/7 Security", "Backup Generator", "Elevator"]),
        "proximity": body.get("proximity", [
            {"name": "Metro Station", "dist": "0.5 km"},
            {"name": "Hospital", "dist": "1.0 km"}
        ]),
        "images": body.get("images") or [body.get("image", "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=600&q=80")],
        "brochure_url": body.get("brochure_url", ""),
    }

    new_record = ProjectRecord(
        project_id=project_id,
        name=name,
        location=location,
        price=price,
        price_val=body.get("price_val", 10000000),
        bedrooms=bedrooms,
        description=body.get("description", f"Premium {bedrooms} BHK property in {location}."),
        features=features,
    )

    try:
        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)
        return {
            "success": True,
            "message": "Project created successfully",
            "project": _format_db_project(new_record),
            "tenantId": auth["tenant_id"],
        }
    except Exception as err:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create project: {err}")
