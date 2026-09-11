"""Property Repository — Canonical Source of Truth for GLG Assets Real Estate Properties.

Architecture Rule: Prompts define behavior; this repository defines facts.
All agents (Property, Email, Social, FAQ, Chat) query this repository.
"""
from typing import Any, Dict, List, Optional
from copy import deepcopy


CANONICAL_PROPERTIES: List[Dict[str, Any]] = [
    {
        "id": "proj_gulshan_luxe",
        "name": "GLG Gulshan Heights",
        "location": {
            "area": "Gulshan 2",
            "city": "Dhaka",
            "country": "Bangladesh",
            "formatted": "Gulshan 2, Dhaka, Bangladesh",
        },
        "pricing": {
            "currency": "BDT",
            "amount": 9500000,
            "display_bn": "৳৯৫ লক্ষ",
            "display_en": "95 Lakhs BDT (৳9,500,000)",
            "effective_from": "2026-09-01",
        },
        "facts": {
            "bedrooms": 3,
            "bathrooms": 3,
            "size_sqft": None,
            "handover_date": "December 2027",
            "amenities": ["Rooftop Garden", "Gym", "Elevator", "Backup Generator", "24/7 Security", "Dedicated Parking"],
        },
        "description": "Exclusive 3 BHK luxury apartment in Gulshan 2 with modern architectural design, private balconies, and round-the-clock security.",
        "brochure_url": "https://example.com/brochures/gulshan_heights.pdf",
        "images": ["https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800"],
        "status": "active",
    },
    {
        "id": "proj_gulshan_palace",
        "name": "GLG Grand Residency",
        "location": {
            "area": "Gulshan 1",
            "city": "Dhaka",
            "country": "Bangladesh",
            "formatted": "Gulshan 1, Dhaka, Bangladesh",
        },
        "pricing": {
            "currency": "BDT",
            "amount": 8500000,
            "display_bn": "৳৮৫ লক্ষ",
            "display_en": "85 Lakhs BDT (৳8,500,000)",
            "effective_from": "2026-09-01",
        },
        "facts": {
            "bedrooms": 2,
            "bathrooms": 2,
            "size_sqft": None,
            "handover_date": "June 2027",
            "amenities": ["Lake View", "24/7 Security", "Backup Generator", "Intercom Facility"],
        },
        "description": "Elegant 2 BHK apartment near Gulshan Lake, in close proximity to premier international schools and diplomatic zones.",
        "brochure_url": "https://example.com/brochures/grand_residency.pdf",
        "images": ["https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800"],
        "status": "active",
    },
    {
        "id": "proj_banani_crest",
        "name": "GLG Banani Crest",
        "location": {
            "area": "Banani",
            "city": "Dhaka",
            "country": "Bangladesh",
            "formatted": "Banani, Dhaka, Bangladesh",
        },
        "pricing": {
            "currency": "BDT",
            "amount": 12000000,
            "display_bn": "৳১.২ কোটি",
            "display_en": "1.2 Crore BDT (৳12,000,000)",
            "effective_from": "2026-09-01",
        },
        "facts": {
            "bedrooms": 3,
            "bathrooms": 3,
            "size_sqft": None,
            "handover_date": "March 2028",
            "amenities": ["Infinity Pool", "Concierge Service", "Underground Parking", "Fitness Center"],
        },
        "description": "Contemporary 3 BHK luxury residence located on prime Banani Road, featuring premium finishes and an executive rooftop terrace.",
        "brochure_url": "https://example.com/brochures/banani_crest.pdf",
        "images": ["https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800"],
        "status": "active",
    },
    {
        "id": "proj_baridhara_luxe",
        "name": "GLG Luxe Heights",
        "location": {
            "area": "Baridhara Diplomatic Zone",
            "city": "Dhaka",
            "country": "Bangladesh",
            "formatted": "Baridhara Diplomatic Zone, Dhaka, Bangladesh",
        },
        "pricing": {
            "currency": "BDT",
            "amount": 18000000,
            "display_bn": "৳১.৮ কোটি",
            "display_en": "1.8 Crore BDT (৳18,000,000)",
            "effective_from": "2026-09-01",
        },
        "facts": {
            "bedrooms": 4,
            "bathrooms": 4,
            "size_sqft": None,
            "handover_date": "December 2028",
            "amenities": ["Lake View", "Infinity Pool", "Smart Home Automation", "24/7 Security", "Private Elevator Access"],
        },
        "description": "Ultra-exclusive 4 BHK diplomatic residence overlooking Baridhara lake with integrated smart-home automation and high-level privacy.",
        "brochure_url": "https://example.com/brochures/luxe_heights.pdf",
        "images": ["https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800"],
        "status": "active",
    },
]

SUPPORTED_MARKET = {
    "country": "Bangladesh",
    "primary_city": "Dhaka",
    "enabled_areas": [
        "Gulshan",
        "Gulshan 1",
        "Gulshan 2",
        "Banani",
        "Baridhara",
        "Baridhara Diplomatic Zone",
        "Dhanmondi",
        "Uttara",
    ],
}


class PropertyRepository:
    """Canonical repository for real estate properties, pricing, and specs."""

    def __init__(self, properties: Optional[List[Dict[str, Any]]] = None):
        self._properties = properties or CANONICAL_PROPERTIES

    def get_all(self) -> List[Dict[str, Any]]:
        """Returns deep copy of all canonical properties."""
        return deepcopy(self._properties)

    def get_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Fetch project by ID."""
        for p in self._properties:
            if p["id"].lower() == project_id.lower():
                return deepcopy(p)
        return None

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetch project by approximate name match."""
        name_clean = name.lower().replace("glg", "").strip()
        for p in self._properties:
            p_name_clean = p["name"].lower().replace("glg", "").strip()
            if name_clean in p_name_clean or p_name_clean in name_clean:
                return deepcopy(p)
        return None

    def search(
        self,
        query: str = "",
        location: Optional[str] = None,
        max_budget: Optional[int] = None,
        bedrooms: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search canonical properties by location, budget, and bedroom count."""
        results = []
        query_clean = query.lower()
        search_loc = (location or "").lower().strip()

        for p in self._properties:
            p_loc_area = p["location"]["area"].lower()
            p_loc_city = p["location"]["city"].lower()
            p_name = p["name"].lower()
            p_desc = p["description"].lower()
            p_price = p["pricing"]["amount"]
            p_beds = p["facts"]["bedrooms"]

            # Filter by location
            if search_loc:
                if search_loc not in p_loc_area and search_loc not in p_loc_city:
                    continue
            elif any(area.lower() in query_clean for area in ["gulshan", "banani", "baridhara"]):
                matched = False
                for area in ["gulshan 2", "gulshan 1", "gulshan", "banani", "baridhara"]:
                    if area in query_clean and area in p_loc_area:
                        matched = True
                        break
                if not matched and not any(k in query_clean for k in [p_name, p["id"]]):
                    continue

            # Filter by budget
            if max_budget and p_price > max_budget:
                continue

            # Filter by bedrooms
            if bedrooms and p_beds != bedrooms:
                continue

            results.append(deepcopy(p))

        return results

    def get_current_price(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve verified pricing data for a project."""
        proj = self.get_by_id(project_id)
        if proj:
            return proj.get("pricing")
        return None

    def get_project_facts(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve verified physical facts for a project."""
        proj = self.get_by_id(project_id)
        if proj:
            return proj.get("facts")
        return None

    def is_supported_location(self, location_name: str) -> bool:
        """Check if location is within supported Bangladesh operating scope."""
        loc_clean = location_name.lower().strip()
        for area in SUPPORTED_MARKET["enabled_areas"]:
            if area.lower() in loc_clean or loc_clean in area.lower():
                return True
        return False

    def to_legacy_dict_format(self) -> List[Dict[str, Any]]:
        """Provides backward-compatible flat dict format for tools and legacy agents."""
        legacy = []
        for p in self._properties:
            legacy.append({
                "id": p["id"],
                "name": p["name"],
                "location": p["location"]["formatted"],
                "price": p["pricing"]["display_en"],
                "price_bn": p["pricing"]["display_bn"],
                "price_val": p["pricing"]["amount"],
                "bedrooms": p["facts"]["bedrooms"],
                "bathrooms": p["facts"]["bathrooms"],
                "description": p["description"],
                "amenities": p["facts"]["amenities"],
                "brochure_url": p["brochure_url"],
                "images": p["images"],
            })
        return legacy


property_repository = PropertyRepository()
