"""Projects API — GET /api/projects, GET /api/project/{id}, and POST /api/projects.

Backed by Supabase/PostgreSQL ProjectRecord with in-memory fallback.
"""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.property_agent import property_agent
from app.core.two_tier_cache import two_tier_cache
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
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_session),
    auth: dict = Depends(_auth)
):
    """Return all available projects from Supabase PostgreSQL, with L1/L2 caching & ETag."""
    tenant_id = auth.get("tenant_id", "glg-default")
    cache_key = f"projects:all:{tenant_id}"

    # 1. Check L1/L2 Cache
    cached_payload = await two_tier_cache.get(cache_key)
    if cached_payload:
        etag = two_tier_cache.generate_etag(cached_payload)
        if_none_match = request.headers.get("if-none-match")
        if if_none_match and if_none_match.strip() == etag:
            response.status_code = status.HTTP_304_NOT_MODIFIED
            return response

        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=120"
        response.headers["X-Cache"] = "HIT"
        return cached_payload

    # 2. Query database with fallback
    result_data = None
    try:
        stmt = select(ProjectRecord).order_by(ProjectRecord.created_at.desc())
        res = await db.execute(stmt)
        records = res.scalars().all()
        if records:
            formatted = [_format_db_project(p) for p in records]
            result_data = {
                "success": True,
                "projects": formatted,
                "count": len(formatted),
                "source": "database",
                "tenantId": tenant_id,
            }
    except Exception:
        pass

    if not result_data:
        # Fallback to canonical repository
        projects = await property_agent.get_projects()
        result_data = {
            "success": True,
            "projects": projects,
            "count": len(projects),
            "source": "canonical_fallback",
            "tenantId": tenant_id,
        }

    # Store in L1/L2 cache (5 min TTL)
    await two_tier_cache.set(cache_key, result_data, ttl=300)

    etag = two_tier_cache.generate_etag(result_data)
    if_none_match = request.headers.get("if-none-match")
    if if_none_match and if_none_match.strip() == etag:
        response.status_code = status.HTTP_304_NOT_MODIFIED
        return response

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=120"
    response.headers["X-Cache"] = "MISS"
    return result_data


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

        # Invalidate L1/L2 projects cache and semantic query cache
        await two_tier_cache.invalidate("projects:all:*")
        from app.core.semantic_cache import semantic_cache
        await semantic_cache.invalidate_by_intent("property_search")

        return {
            "success": True,
            "message": "Project created successfully",
            "project": _format_db_project(new_record),
            "tenantId": auth["tenant_id"],
        }
    except Exception as err:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create project: {err}")
