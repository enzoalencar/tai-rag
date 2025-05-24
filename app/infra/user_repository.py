from app.interfaces.repositories import UserRepositoryInterface
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas import CreateUser


class UserRepository(UserRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, email: str) -> User:
        user = User(name=name, email=email)
        self.session.add(user)
        await self.session.flush()
        return user