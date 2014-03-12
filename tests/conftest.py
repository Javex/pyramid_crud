from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Column, Integer, Table, MetaData, ForeignKey
from sqlalchemy.orm import mapper, relationship
import pytest


@pytest.fixture
def Base(metadata):

    class _Base(object):
        @declared_attr
        def __tablename__(cls):
            return cls.__name__.lower()

    Base = declarative_base(cls=_Base, metadata=metadata)

    return Base


@pytest.fixture
def metadata():
    return MetaData()


@pytest.fixture(params=['declarative', 'classical'])
def Model_one_pk(Base, request, metadata):
    if request.param == 'declarative':
        class Model(Base):
            id = Column(Integer, primary_key=True)
    else:
        table = Table(
            'model', metadata,
            Column('id', Integer, primary_key=True))

        class Model(object):
            pass
        mapper(Model, table)
    return Model


@pytest.fixture(params=['declarative', 'classical'])
def Model_two_pk(Base, request, metadata):
    if request.param == 'declarative':
        class Model(Base):
            id = Column(Integer, primary_key=True)
            id2 = Column(Integer, primary_key=True)
    else:
        table = Table(
            'model', metadata,
            Column('id', Integer, primary_key=True),
            Column('id2', Integer, primary_key=True))

        class Model(object):
            pass
        mapper(Model, table)
    return Model


@pytest.fixture(params=['declarative', 'classical'])
def Model_diff_colname(Base, request, metadata):
    if request.param == 'declarative':
        class Model(Base):
            id = Column('id2', Integer, primary_key=True)
    else:
        table = Table(
            'model', metadata,
            Column('id2', Integer, primary_key=True))

        class Model(object):
            pass
        mapper(Model, table, properties={'id': table.c.id2})
    return Model


@pytest.fixture(params=['declarative', 'classical'])
def Model2_basic(Base, request, metadata):
    if request.param == 'declarative':
        class Model2(Base):
            id = Column(Integer, primary_key=True)
    else:
        table = Table(
            'model2', metadata,
            Column('id', Integer, primary_key=True))

        class Model2(object):
            pass
        mapper(Model2, table)
    return Model2


@pytest.fixture(params=['declarative', 'classical'])
def Model2_many_to_one(Base, request, Model_one_pk, metadata):
    if request.param == 'declarative':
        class Model2(Base):
            id = Column(Integer, primary_key=True)
            model_id = Column(ForeignKey('model.id'))
            model = relationship(Model_one_pk, backref='models')
    else:
        table = Table(
            'model2', metadata,
            Column('id', Integer, primary_key=True),
            Column('model_id', ForeignKey('model.id')))

        class Model2(object):
            pass
        mapper(Model2, table, properties={
            'model': relationship(Model_one_pk, backref='models')
        })
    return Model2


@pytest.fixture(params=['declarative', 'classical'])
def Model2_many_to_one_multiple(Base, request, Model_one_pk, metadata):
    if request.param == 'declarative':
        class Model2(Base):
            id = Column(Integer, primary_key=True)
            model_id1 = Column(ForeignKey('model.id'))
            model_id2 = Column(ForeignKey('model.id'))
            model1 = relationship(Model_one_pk, backref='models1',
                                  foreign_keys=[model_id1])
            model2 = relationship(Model_one_pk, backref='models2',
                                  foreign_keys=[model_id2])
    else:
        table = Table(
            'model2', metadata,
            Column('id', Integer, primary_key=True),
            Column('model_id1', ForeignKey('model.id')),
            Column('model_id2', ForeignKey('model.id')))

        class Model2(object):
            pass
        mapper(Model2, table, properties={
            'model1': relationship(Model_one_pk, backref='models1',
                                   foreign_keys=[table.c.model_id1]),
            'model2': relationship(Model_one_pk, backref='models2',
                                   foreign_keys=[table.c.model_id2])
        })
    return Model2
