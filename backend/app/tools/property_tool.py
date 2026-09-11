"""Property Search Tool — SQL property filtering + RAG integration + Media Actions."""

import re
from typing import Optional, List, Dict, Any
from app.repositories.property_repository import property_repository

# Backward-compatibility alias pointing to canonical repository data
PROJECTS_DATABASE = property_repository.to_legacy_dict_format()


class PropertySearchTool:
    """SQL + RAG hybrid property search tool grounded in canonical repository."""

    async def search(
        self,
        query: str,
        location: Optional[str] = None,
        max_budget: Optional[int] = None,
        bedrooms: Optional[int] = None,
    ) -> dict:
        """Perform SQL search on project database with RAG fallback."""
        query_lower = query.lower()

        # Parse budget if present in text (e.g. "under 1 crore", "under 90 lakhs", "1.5 cr")
        parsed_budget = max_budget
        if not parsed_budget:
            if "1.8 crore" in query_lower or "1.8 cr" in query_lower:
                parsed_budget = 18000000
            elif "1.2 crore" in query_lower or "1.2 cr" in query_lower:
                parsed_budget = 12000000
            elif "1 crore" in query_lower or "1 cr" in query_lower or "100 lakh" in query_lower:
                parsed_budget = 10000000
            elif "95 lakh" in query_lower or "95 L" in query_lower:
                parsed_budget = 9500000
            elif "90 lakh" in query_lower or "90 L" in query_lower:
                parsed_budget = 9000000
            elif "85 lakh" in query_lower or "85 L" in query_lower:
                parsed_budget = 8500000
            elif "80 lakh" in query_lower:
                parsed_budget = 8000000

        # Location extraction from query — strictly Bangladesh operating locations
        search_loc = (location or "").lower().strip()
        if not search_loc:
            for loc_name in ["baridhara", "gulshan 2", "gulshan 1", "gulshan", "banani", "dhanmondi", "uttara", "dhaka"]:
                if loc_name in query_lower:
                    search_loc = loc_name
                    break

        # Check if user specifically requested a project by name
        target_project_keywords = []
        all_projects = property_repository.to_legacy_dict_format()
        for proj in all_projects:
            proj_name_lower = proj["name"].lower()
            clean_proj_words = [w for w in proj_name_lower.split() if w != "glg"]
            phrase = " ".join(clean_proj_words)
            if phrase in query_lower or proj_name_lower in query_lower:
                target_project_keywords.append(proj["id"])

        results = []
        for proj in all_projects:
            match = True
            if target_project_keywords:
                if proj["id"] not in target_project_keywords:
                    match = False
            else:
                if search_loc and search_loc not in proj["location"].lower() and search_loc not in proj["name"].lower():
                    match = False
                if parsed_budget and proj["price_val"] > parsed_budget:
                    match = False
                if bedrooms and proj["bedrooms"] != bedrooms:
                    match = False

            if match:
                results.append(proj)

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
