from app.interfaces.repositories import ContextRepositoryInterface
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Context


class ContextRepository(ContextRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_title(self, title: str) -> Context | None:
        query = select(Context).where(Context.title == title).limit(1)

        res = await self.session.execute(query)
        return res.first()