from app.models import Conversation


class ConversationRepository:
    def __init__(self, session):
        self.session = session

    async def get_by(self, name):
        return self.session.query(Conversation).filter_by(name=name).first()