from pydantic import BaseModel
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


    class Config:
        orm_mode = True
