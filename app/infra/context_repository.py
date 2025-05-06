from sqlalchemy import select

from app.models import Context


class ContextRepository:
    def __init__(self, session):
        self.session = session

    async def get_by_title(self, title: str) -> Context | None:
        query = select(Context).where(Context.title == title).limit(1)

        res = await self.session.execute(query)
        return res.first()