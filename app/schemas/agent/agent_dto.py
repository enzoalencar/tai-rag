from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AgentDTO(BaseModel):
    id: UUID
    name: str
    model: str
    config: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)