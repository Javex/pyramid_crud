from sqlalchemy import (
    Column,
    Integer,
    Unicode,
    DateTime,
    Boolean,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref,
    )

from sqlalchemy.schema import (
    ForeignKey,
    )

from datetime import datetime

from pyramid.events import NewRequest, subscriber

DBSession = scoped_session(sessionmaker())
Base = declarative_base()


class Poll(Base):
    __tablename__ = 'poll'
    id = Column(Integer, primary_key=True)
    question = Column(Unicode, nullable=False, info={'label': 'Question'})
    pub_date = Column(DateTime, nullable=False, default=datetime.utcnow,
                      info={'label': 'Date Published'})
    published = Column(Boolean, default=False, info={'label': 'Published?'})


class Choice(Base):
    __tablename__ = 'choice'
    id = Column(Integer, primary_key=True)
    poll_id = Column(ForeignKey(Poll.id), nullable=False)
    choice_text = Column(Unicode, nullable=False, unique=True,
                         info={'label': 'Choice Text'})
    votes = Column(Integer, default=0,
                   info={'label': 'Votes'})

    poll = relationship("Poll",
                        backref=backref("choices",
                                        cascade="all, delete-orphan"))


class Test(Base):
    __tablename__ = 'test'
    poll_id = Column(ForeignKey(Poll.id), primary_key=True)
    choice_id = Column(ForeignKey(Choice.id), primary_key=True)


@subscriber(NewRequest)
def create_session(event):
    event.request.dbsession = DBSession
