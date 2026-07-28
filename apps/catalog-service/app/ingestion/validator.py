from typing import Any, Dict, List, Tuple
from app.schemas.movies import MovieIngestSchema

def validate_normalized_movies(
    normalized_list: List[Dict[str, Any]]
) -> Tuple[List[MovieIngestSchema], List[Tuple[Dict[str, Any], str]]]:
    """
    Validates all movies against the MovieIngestSchema.
    Returns:
        tuple: (list of valid MovieIngestSchema, list of tuples (raw_data, error_message))
    """
    valid: List[MovieIngestSchema] = []
    failed: List[Tuple[Dict[str, Any], str]] = []

    for item in normalized_list:
        try:
            validated = MovieIngestSchema(**item)
            valid.append(validated)
        except Exception as e:
            failed.append((item, str(e)))

    return valid, failed
