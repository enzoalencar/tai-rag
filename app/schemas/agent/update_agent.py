from typing import Optional
from pydantic import BaseModel


class UpdateAgent(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    config: Optional[str] = None