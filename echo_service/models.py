from pydantic import BaseModel

try:
    from pydantic import ConfigDict
except Exception:
    # Backwards-compatible fallback for Pydantic<2 where ConfigDict doesn't exist
    class ConfigDict(dict):
        pass


from typing import Any, Dict, Optional


class WebhookEntry(BaseModel):
    id: str
    received_at: str
    method: str
    path: str
    client_ip: Optional[str]
    user_agent: Optional[str]
    headers: Dict[str, str]
    body: Any
    raw_body: Optional[str]

    # Pydantic v2 migration: use ConfigDict and 'from_attributes' instead of legacy Config
    model_config = ConfigDict(from_attributes=True)
