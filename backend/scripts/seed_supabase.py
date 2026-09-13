"""Seed script to populate Supabase/PostgreSQL with canonical real-estate assets and system data.

Usage:
    python -m scripts.seed_supabase
"""
import asyncio
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.database import async_session_factory, init_db, check_connection
from app.models.models import ProjectRecord, UserRecord, MediaRecord
from app.models.user import UserRole

CANONICAL_SEED_PROJECTS = [
    {
        "project_id": "proj_gulshan_heights",
        "name": "GLG Gulshan Heights",
        "location": "Gulshan 2, Dhaka",
        "price": "৳95 Lakhs - ৳1.8 Crore",
        "price_val": 9500000,
        "bedrooms": 3,
        "description": "Exclusive 3 & 4 BHK luxury apartment in Gulshan 2 with modern architectural design, private balconies, and round-the-clock security.",
        "features": {
            "lat": 23.7925,
            "lng": 90.4078,
            "status": "Ready / Available",
            "price_short": "৳95L+",
            "valuation": "৳14.8 Cr",
            "units_available": 4,
            "total_units": 16,
            "handover_date": "December 2027",
            "amenities": ["Rooftop Infinity Pool", "24/7 Generator Backup", "Basement Parking", "Smart Home Tech", "Gym & Fitness Studio"],
            "proximity": [
                {"name": "United Hospital", "dist": "1.2 km"},
                {"name": "Gulshan Club", "dist": "0.5 km"},
                {"name": "Diplomatic Zone", "dist": "0.3 km"}
            ],
            "images": [
                "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=800&q=80"
            ],
            "brochure_url": "https://example.com/brochures/gulshan_heights.pdf"
        }
    },
    {
        "project_id": "proj_banani_crest",
        "name": "GLG Banani Crest",
        "location": "Banani Block F, Dhaka",
        "price": "৳1.2 Crore - ৳2.5 Crore",
        "price_val": 12000000,
        "bedrooms": 4,
        "description": "Contemporary luxury duplexes located on prime Banani Road, featuring Italian marble finishes and an executive rooftop terrace.",
        "features": {
            "lat": 23.7937,
            "lng": 90.4046,
            "status": "Under Construction",
            "price_short": "৳1.2Cr+",
            "valuation": "৳9.2 Cr",
            "units_available": 3,
            "total_units": 10,
            "handover_date": "March 2028",
            "amenities": ["Duplex Terrace", "Italian Marble", "Double Height Lobby", "Private Elevator", "Concierge Service"],
            "proximity": [
                {"name": "Banani Metro Rail", "dist": "0.6 km"},
                {"name": "Kemal Ataturk Ave", "dist": "0.2 km"},
                {"name": "Banani Club", "dist": "0.4 km"}
            ],
            "images": [
                "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80"
            ],
            "brochure_url": "https://example.com/brochures/banani_crest.pdf"
        }
    },
    {
        "project_id": "proj_baridhara_luxe",
        "name": "GLG Baridhara Diplomatic Luxe",
        "location": "Baridhara Diplomatic Zone, Dhaka",
        "price": "৳3.5 Crore - ৳5.8 Crore",
        "price_val": 35000000,
        "bedrooms": 5,
        "description": "Ultra-exclusive residency in Dhaka's premier diplomatic enclave with high-security perimeters, diplomatic clearance, and lake views.",
        "features": {
            "lat": 23.7998,
            "lng": 90.4215,
            "status": "High Demand",
            "price_short": "৳3.5Cr+",
            "valuation": "৳18.5 Cr",
            "units_available": 8,
            "total_units": 12,
            "handover_date": "November 2028",
            "amenities": ["Diplomatic Security", "Private Elevator", "Lake View Deck", "Heated Pool", "Helipad Access"],
            "proximity": [
                {"name": "US Embassy", "dist": "0.4 km"},
                {"name": "Baridhara Lake Park", "dist": "0.1 km"},
                {"name": "American Club", "dist": "0.3 km"}
            ],
            "images": [
                "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=800&q=80"
            ],
            "brochure_url": "https://example.com/brochures/baridhara_luxe.pdf"
        }
    },
    {
        "project_id": "proj_grand_residency",
        "name": "GLG Grand Residency",
        "location": "Dhanmondi 27, Dhaka",
        "price": "৳85 Lakhs - ৳1.4 Crore",
        "price_val": 8500000,
        "bedrooms": 3,
        "description": "Elegant 2 & 3 BHK apartments near Dhanmondi Lake, close to international schools, shopping, and healthcare centers.",
        "features": {
            "lat": 23.7461,
            "lng": 90.3742,
            "status": "Handover 2026",
            "price_short": "৳85L+",
            "valuation": "৳7.6 Cr",
            "units_available": 6,
            "total_units": 14,
            "handover_date": "June 2027",
            "amenities": ["Gym & Fitness Studio", "Kids Play Zone", "Community Hall", "Full CCTV", "Backup Generator"],
            "proximity": [
                {"name": "Dhanmondi Lake", "dist": "0.4 km"},
                {"name": "Rapa Plaza", "dist": "0.2 km"},
                {"name": "Square Hospital", "dist": "1.5 km"}
            ],
            "images": [
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80"
            ],
            "brochure_url": "https://example.com/brochures/grand_residency.pdf"
        }
    },
    {
        "project_id": "proj_uttara_sky",
        "name": "GLG Uttara Sky Villas",
        "location": "Uttara Sector 3, Dhaka",
        "price": "৳75 Lakhs - ৳1.3 Crore",
        "price_val": 7500000,
        "bedrooms": 3,
        "description": "Modern urban apartments right on the Metro Rail corridor with rapid connectivity to Hazrat Shahjalal International Airport.",
        "features": {
            "lat": 23.8690,
            "lng": 90.3980,
            "status": "Upcoming Launch",
            "price_short": "৳75L+",
            "valuation": "৳6.2 Cr",
            "units_available": 10,
            "total_units": 20,
            "handover_date": "December 2028",
            "amenities": ["Sky Garden", "EV Charging Station", "Infinity Jacuzzi", "Solar Backup", "Smart Keyless Entry"],
            "proximity": [
                {"name": "Uttara Metro Station", "dist": "0.5 km"},
                {"name": "Dhaka Int. Airport", "dist": "2.5 km"},
                {"name": "Sector 3 Park", "dist": "0.1 km"}
            ],
            "images": [
                "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=800&q=80"
            ],
            "brochure_url": "https://example.com/brochures/uttara_sky.pdf"
        }
    }
]


async def run_seed():
    print("[Seed] Checking database connection...")
    is_up = await check_connection()
    if not is_up:
        print("[Seed] ERROR: Database connection failed. Please verify DATABASE_URL in .env.")
        return False

    print("[Seed] Ensuring schema and extensions exist in Supabase/PostgreSQL...")
    await init_db()

    async with async_session_factory() as session:
        print("[Seed] Upserting canonical real estate developments...")
        for proj_data in CANONICAL_SEED_PROJECTS:
            stmt = select(ProjectRecord).where(ProjectRecord.project_id == proj_data["project_id"])
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                existing.name = proj_data["name"]
                existing.location = proj_data["location"]
                existing.price = proj_data["price"]
                existing.price_val = proj_data["price_val"]
                existing.bedrooms = proj_data["bedrooms"]
                existing.description = proj_data["description"]
                existing.features = proj_data["features"]
            else:
                new_proj = ProjectRecord(
                    project_id=proj_data["project_id"],
                    name=proj_data["name"],
                    location=proj_data["location"],
                    price=proj_data["price"],
                    price_val=proj_data["price_val"],
                    bedrooms=proj_data["bedrooms"],
                    description=proj_data["description"],
                    features=proj_data["features"],
                )
                session.add(new_proj)

        await session.commit()
        print(f"[Seed] Successfully seeded {len(CANONICAL_SEED_PROJECTS)} projects into Supabase/PostgreSQL.")
        return True


if __name__ == "__main__":
    success = asyncio.run(run_seed())
    sys.exit(0 if success else 1)
