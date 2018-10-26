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

Session = sessionmaker()


def init(settings):
    engine = create_engine(settings['url'])
    Session.configure(bind=engine)
    return engine


Base = declarative_base()


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    params = Column(Text)
    status = Column(String, default='new')
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Task(name='{self.name}', status='{self.status}')>"
