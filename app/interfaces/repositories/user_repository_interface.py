from typing import Protocol
from app.models import User
from app.schemas import CreateUser


class UserRepositoryInterface(Protocol):
    async def create(self, request: CreateUser) -> User: ...
