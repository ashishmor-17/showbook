import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def normalize_movie(raw: Dict[str, Any], ingestion_run_id: str, source: str = "SCRAPED") -> Dict[str, Any]:
    """
    Transforms raw scraped partner movie data to match DB column naming & structures.
    """
    # Map source parameter to database check constraints: 'SCRAPED', 'MANUAL', 'PARTNER_API'
    db_source = "SCRAPED"
    src_upper = source.upper()
    if src_upper in ("SCRAPED", "SCRAPER"):
        db_source = "SCRAPED"
    elif src_upper in ("PARTNER_API", "PARTNER_JSON", "PARTNER"):
        db_source = "PARTNER_API"
    elif src_upper == "MANUAL":
        db_source = "MANUAL"

    cast_list = []
    for member in raw.get("cast", []):
        cast_list.append({"name": member, "role": "Actor"})
        
    crew_list = []
    raw_crew = raw.get("crew") or {}
    for role, name in raw_crew.items():
        if name:
            crew_list.append({"name": name, "role": role.capitalize()})
            
    return {
        "title": raw.get("title"),
        "slug": raw.get("slug"),
        "description": raw.get("synopsis"),
        "language": raw.get("language"),
        "genre": raw.get("genre", []),
        "duration_minutes": raw.get("duration_minutes"),
        "rating": raw.get("rating"),
        "release_date": raw.get("release_date"),
        "poster_url": raw.get("poster_url"),
        "banner_url": raw.get("banner_url"),
        "trailer_url": raw.get("trailer_url"),
        "cast": cast_list,
        "crew": crew_list,
        "source": db_source,
        "ingestion_id": ingestion_run_id,
        "is_active": True
    }
