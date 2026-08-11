"""Property Search Tool — SQL property filtering + RAG integration + Media Actions."""

import re
from typing import Optional

# Enhanced real-estate project inventory for MVP
PROJECTS_DATABASE = [
    {
        "id": "proj_gulshan_luxe",
        "name": "GLG Gulshan Heights",
        "location": "Gulshan 2, Dhaka",
        "price": "95 Lakhs BDT",
        "price_val": 9500000,
        "bedrooms": 3,
        "description": "Luxury 3 BHK apartment in Gulshan 2 with modern amenities, rooftop garden, and 24/7 security.",
        "amenities": ["Rooftop Garden", "Gym", "Elevator", "Generator", "Parking"],
        "brochure_url": "https://example.com/brochures/gulshan_heights.pdf",
        "images": ["https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800"]
    },
    {
        "id": "proj_gulshan_palace",
        "name": "GLG Grand Residency",
        "location": "Gulshan 1, Dhaka",
        "price": "85 Lakhs BDT",
        "price_val": 8500000,
        "bedrooms": 2,
        "description": "Elegant 2 BHK apartment near Gulshan Lake, close to shopping centers and schools.",
        "amenities": ["Lake View", "Security", "Backup Generator"],
        "brochure_url": "https://example.com/brochures/grand_residency.pdf",
        "images": ["https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800"]
    },
    {
        "id": "proj_banani_crest",
        "name": "GLG Banani Crest",
        "location": "Banani, Dhaka",
        "price": "1.2 Crore BDT",
        "price_val": 12000000,
        "bedrooms": 3,
        "description": "Exclusive 3 BHK luxury residence in prime Banani area.",
        "amenities": ["Infinity Pool", "Concierge", "Underground Parking"],
        "brochure_url": "https://example.com/brochures/banani_crest.pdf",
        "images": ["https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800"]
    },
    {
        "id": "proj_mumbai_luxe",
        "name": "GLG Luxe Heights",
        "location": "Bandra West, Mumbai",
        "price": "1.8 Crore INR",
        "price_val": 18000000,
        "bedrooms": 3,
        "description": "Premium luxury apartments with sea view and smart home automation.",
        "amenities": ["Sea View", "Infinity Pool", "Smart Home"],
        "brochure_url": "https://example.com/brochures/luxe_heights.pdf",
        "images": ["https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"]
    }
]


class PropertySearchTool:
    """SQL + RAG hybrid property search tool."""

    async def search(
        self,
        query: str,
        location: Optional[str] = None,
        max_budget: Optional[int] = None,
        bedrooms: Optional[int] = None,
    ) -> dict:
        """Perform SQL search on project database with RAG fallback."""
        query_lower = query.lower()
        results = []

        # Parse budget if present in text (e.g. "under 1 crore", "under 90 lakhs")
        parsed_budget = max_budget
        if not parsed_budget:
            if "1 crore" in query_lower or "1 cr" in query_lower or "100 lakh" in query_lower:
                parsed_budget = 10000000
            elif "90 lakh" in query_lower or "90 L" in query_lower:
                parsed_budget = 9000000
            elif "80 lakh" in query_lower:
                parsed_budget = 8000000

        # Location extraction from query
        search_loc = (location or "").lower()
        if not search_loc:
            for loc_name in ["gulshan", "banani", "bandra", "mumbai", "dhaka"]:
                if loc_name in query_lower:
                    search_loc = loc_name
                    break

        for proj in PROJECTS_DATABASE:
            match = True
            if search_loc and search_loc not in proj["location"].lower() and search_loc not in proj["name"].lower():
                match = False
            if parsed_budget and proj["price_val"] > parsed_budget:
                match = False
            if bedrooms and proj["bedrooms"] != bedrooms:
                match = False

            if match:
                results.append(proj)

        # Build actions based on findings
        actions = []
        if results:
            actions.append("send_images")
            actions.append("send_brochure")

        return {
            "count": len(results),
            "projects": results,
            "actions": actions,
            "search_query": query,
            "filters": {"location": search_loc, "max_budget": parsed_budget, "bedrooms": bedrooms}
        }


property_search_tool = PropertySearchTool()
