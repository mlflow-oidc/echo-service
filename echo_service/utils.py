from typing import Any


def model_to_dict(m: Any) -> dict:
    """Return a dict representation of a Pydantic model compatible with v1 and v2.

    Tries v2's model_dump(), falls back to v1's dict().
    """
    # v2
    if hasattr(m, "model_dump"):
        try:
            return m.model_dump()
        except Exception:
            pass
    # v1
    if hasattr(m, "dict"):
        try:
            return m.dict()
        except Exception:
            pass
    # Fallback: try to convert using __dict__
    return dict(getattr(m, "__dict__", {}))
