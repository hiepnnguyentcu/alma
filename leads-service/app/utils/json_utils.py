"""JSON serialization utilities."""
from datetime import datetime
from typing import Any
from uuid import UUID


def make_json_safe(obj: Any) -> Any:
    """Convert objects to JSON-serializable format.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    else:
        return obj
