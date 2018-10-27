from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

session_factory = sessionmaker()


def init(settings):
    engine = create_engine(settings['url'])
    session_factory.configure(bind=engine)
    return engine


Base = declarative_base()


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    params = Column(Text)
    status = Column(String, default='new')
    result = Column(Text)
    files = Column(Text)
    email = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Task(name='{self.name}', params='{self.params[:10]}...', status='{self.status}')>"


globals_sessions = [session_factory()]
