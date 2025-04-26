from pydantic import BaseModel


class CreateAgent(BaseModel):
    name: str
    model: str
    config: str