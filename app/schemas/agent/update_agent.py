from typing import Optional
from pydantic import BaseModel


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    config: Optional[str] = None