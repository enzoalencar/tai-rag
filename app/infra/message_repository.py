from app.interfaces.repositories import MessageRepositoryInterface
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas import CreateUser


class MessageRepository(MessageRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, request: CreateUser):
        pass