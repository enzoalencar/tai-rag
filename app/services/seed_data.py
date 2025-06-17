from datetime import datetime
from app.config import settings
from app.models import Agent, Context
from sqlalchemy.orm import Session

from app.schemas.agent.create_agent import CreateAgent
from app.schemas.context.create_context import CreateContext


class SeedData:
    def __init__(self, session: Session, created_time):
        self.session = session
        self.created_time = created_time

    def seed_agents(self):
        request : CreateAgent = CreateAgent(name='OpenAI', model=settings.MODEL, config="")

        exists = self.session.query(Agent).filter(Agent.name == request.name).first()
        if not exists:
            agent = Agent(**request.model_dump())
            self.session.add(agent)

    def seed_contexts(self):
        contexts: list[CreateContext] = [
            CreateContext(
                title="Coffee",
                description="conversation about coffee",
                initial_prompt="What is your favorite coffee?",
            ),
            CreateContext(
                title="Gym",
                description="conversation about gym",
                initial_prompt="What is your favorite gym's exercise?",
            )
        ]

        for context in contexts:
            exists = self.session.query(Context).filter(Context.title == context.title).first()
            if not exists:
                context = Context(**context.model_dump())
                self.session.add(context)

    def run_all(self):
        self.seed_agents()
        self.seed_contexts()
        self.session.commit()

def run_seed_sync(connection):
    session = Session(bind=connection)

    agents_exist = session.query(Agent).first()
    context_exists = session.query(Context).first()

    if not agents_exist or not context_exists:
        seed_data = SeedData(session, datetime.now())
        seed_data.run_all()

    session.close()
