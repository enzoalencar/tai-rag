from app.interfaces.repositories import AgentRepositoryInterface
from app.schemas.agent.agent_dto import AgentDTO
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent


class AgentRepository(AgentRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def exists(self) -> bool:
        query = select(Agent).limit(1)

        res = await self.session.execute(query)
        return res.first() is not None

    async def get_by_name(self, name: str) -> Agent | None:
        query = select(Agent).where(Agent.name == name).limit(1)

        res = await self.session.execute(query)
        return res.first()

    async def get_by_model(self, model: str) -> Agent | None:
        query = select(Agent).where(Agent.model == model).limit(1)

        res = await self.session.execute(query)

        agent = res.scalar_one_or_none()
        return agent