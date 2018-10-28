import math
from datetime import datetime

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


def row2dict(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def paginator(queryset, page, per_page=20, transformer=lambda i: i):
    result = {
        'page_count': math.ceil(queryset.count() / per_page),
        'rows': [],
        'per_page': per_page,
    }

    if result['page_count'] == 0:
        return result

    offset = per_page * (page - 1)
    result['rows'] = [transformer(t) for t in queryset[offset: offset + per_page]]
    return result
