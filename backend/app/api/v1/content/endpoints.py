"""Content Services — Real LLM-based content generation for social media and marketing."""

from fastapi import APIRouter, Depends

from app.dependencies import require_automation_secret as _auth
from app.agents.content_agent import content_agent

router = APIRouter()


@router.post("", summary="Generate multi-platform content (Facebook, Instagram, LinkedIn)")
@router.post("/", summary="Generate multi-platform content (Facebook, Instagram, LinkedIn)")
async def generate_content(body: dict, auth: dict = Depends(_auth)):
    """Generate content for Facebook, Instagram, and LinkedIn in one call.

    Request body:
    {
        "topic": "GLG Gulshan Heights Luxury Apartments",
        "tone": "luxury",
        "keywords": ["gulshan", "luxury", "dhaka"]
    }
    """
    topic = body.get("topic", "real estate property")
    tone = body.get("tone", "luxury")

    fb_caption = (await content_agent.generate_captions(topic, tone, count=1))[0] if await content_agent.generate_captions(topic, tone, count=1) else f"Discover luxury at {topic}."
    ig_hashtags = await content_agent.generate_hashtags(topic, count=10)
    ig_caption = f"{fb_caption}\n\n" + " ".join(ig_hashtags)
    linkedin_post = f"Executive Summary: {topic}\n\nWe are pleased to introduce {topic}, designed for modern living with premium amenities.\n\n#RealEstate #Investment"

    return {
        "success": True,
        "topic": topic,
        "content": {
            "facebook": {
                "text": fb_caption,
                "status": "draft"
            },
            "instagram": {
                "text": ig_caption,
                "hashtags": ig_hashtags,
                "status": "draft"
            },
            "linkedin": {
                "text": linkedin_post,
                "status": "draft"
            }
        },
        "tenantId": auth["tenant_id"],
    }


@router.post("/captions", summary="Generate social media captions")
async def generate_captions(body: dict, auth: dict = Depends(_auth)):
    """Generate social media captions using AI."""
    topic = body.get("topic", "real estate property")
    tone = body.get("tone", "professional")
    count = min(int(body.get("count", 3)), 10)

    captions = await content_agent.generate_captions(topic, tone, count)

    return {
        "success": True,
        "captions": captions,
        "count": len(captions),
        "tenantId": auth["tenant_id"],
    }


@router.post("/hashtags", summary="Generate hashtags")
async def generate_hashtags(body: dict, auth: dict = Depends(_auth)):
    """Generate relevant hashtags for a topic."""
    topic = body.get("topic", "real estate")
    count = min(int(body.get("count", 8)), 20)

    hashtags = await content_agent.generate_hashtags(topic, count)

    return {
        "success": True,
        "hashtags": hashtags,
        "count": len(hashtags),
        "tenantId": auth["tenant_id"],
    }


@router.post("/description", summary="Generate property description")
async def generate_description(body: dict, auth: dict = Depends(_auth)):
    """Generate a property description using AI."""
    project_name = body.get("project_name", "Property")
    location = body.get("location", "")
    features = body.get("features", [])

    description = await content_agent.generate_description(project_name, location, features)

    return {
        "success": True,
        "description": description,
        "project_name": project_name,
        "tenantId": auth["tenant_id"],
    }
