import os
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import (Column, Integer, Table, MetaData, ForeignKey,
                        create_engine)
from sqlalchemy.orm import mapper, relationship, Session
import pytest
import inspect
import logging
from pyramid import testing
from pyramid.asset import abspath_from_asset_spec
from mako.lookup import TemplateLookup
from tests import all_forms, normal_forms, inline_forms
from pyramid_crud import views
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock


@pytest.fixture(autouse=True)
def logger():
    logging.basicConfig()


@pytest.fixture
def csrf_token(session, pyramid_request):
    session.get_csrf_token.return_value = 'ABCD'
    token = pyramid_request.session.get_csrf_token()
    pyramid_request.POST['csrf_token'] = token
    return 'ABCD'


@pytest.fixture
def venusian_init(config):
    context = MagicMock()
    context.config.with_package.return_value = config

    def run_cbs(obj):
        for cb_list in obj.__venusian_callbacks__.values():
            for item in cb_list:
                cb = item[0]
                cb(context, None, None)
    run_cbs.context = context
    return run_cbs


@pytest.fixture(params=[views.ViewConfigurator])
def view_configurator_class(request):
    """Get one of all available view configurators on each invocation thus
    allowing to test multiple configurators so conform to the specification"""
    return request.param


@pytest.fixture(params=['bootstrap'])
def template_setup(config, request):
    module_dir = abspath_from_asset_spec('pyramid_crud:_mako_template_cache')
    config.add_settings({'mako.module_directory': module_dir})
    config.include("pyramid_mako")
    config.commit()


@pytest.fixture
def Base(metadata):

    class _Base(object):
        @declared_attr
        def __tablename__(cls):
            return cls.__name__.lower()

    Base = declarative_base(cls=_Base, metadata=metadata)

    return Base


@pytest.fixture
def engine():
    e = create_engine('sqlite://', echo=True)
    return e


@pytest.fixture
def DBSession(engine):
    return Session(bind=engine)


@pytest.fixture
def pyramid_request():
    request = testing.DummyRequest()
    request.client_addr = '127.0.0.1'
    return request


@pytest.fixture
def session(pyramid_request):
    session = MagicMock()
    pyramid_request.session = session
    return session


@pytest.yield_fixture
def config(pyramid_request, request):
    cfg = testing.setUp(request=pyramid_request, autocommit=False)
    yield cfg
    # Commit to make sure any errors are raised on delayed configuration
    cfg.commit()
    testing.tearDown()


@pytest.fixture
def metadata():
    return MetaData()


@pytest.fixture(params=normal_forms)
def normal_form(request):
    return request.param


@pytest.fixture(params=inline_forms)
def inline_form(request):
    return request.param


@pytest.fixture(params=all_forms)
def any_form(request):
    return request.param


@pytest.fixture(params=['declarative', 'classical'])
def model_factory(request, Base, metadata, engine):
    """A fixture that returns a function to create models. The returned
    function takes the following arguments:

    columns: A list of SQLAlchemy Column instances for the model, defaults
    to an empty list, thus only the defaults will be used.

    name: Name for the model to use. Defaults to "Model".

    defaults: Another list of SA columns. This defaults to a single column
    "id" thus allowing the defaults to create a table with no arguments
    given.

    col_name_to_attr_map: If you want to rename columns, then give this a
    dict with column names as keys and attribute names as values. So, for
    example, if you want to rename the column "id" to "id2" as the
    attribute, then pass "{'id': 'id2'}".

    relationships: A dict of relationships between the tables. As keys use
    the desired attribute name and as value use the actual relationship.
    In case of multiple relationships between two models, see the
    relationship_fks option. In this case, this may also be callables that
    accept a single argument, either a string or a column which will be
    a valid argument for the "foreign_keys" option to "relationship".

    relationship_fks: A map of relationship attribute names (keys) to
    column names on the model. Thus if you want to pass the column
    "model_id1" as the "foreign_keys" argument for "model1" to your
    callable above, pass in "{'model1': 'model_id1'}". This is a necessity
    to enable declarative and classical configuration in a single function.
    """
    def _make_model(columns=None, name='Model',
                    defaults=None,
                    col_name_to_attr_map=None,
                    relationships=None, relationship_fks=None):
        if columns is None:
            columns = []
        if defaults is None:
            defaults = [Column('id', Integer, primary_key=True)]
        if col_name_to_attr_map is None:
            col_name_to_attr_map = {}
        if relationships is None:
            relationships = {}
        if relationship_fks is None:
            relationship_fks = {}

        if request.param == 'declarative':
            attrs = OrderedDict()
            for col in defaults + columns:
                attrs[col_name_to_attr_map.get(col.name, col.name)] = col
            for rel_name, rel in relationships.items():
                if inspect.isfunction(rel):
                    rel_str_name = "%s.%s" % (name, relationship_fks[rel_name])
                    attrs[rel_name] = rel(rel_str_name)
                else:
                    attrs[rel_name] = rel
            Model = type(name, (Base,), attrs)
        else:
            table = Table(name.lower(), metadata, *tuple(defaults + columns))

            properties = {}
            for col_name, attr_name in col_name_to_attr_map.items():
                properties[attr_name] = getattr(table.c, col_name)
            for rel_name, rel in relationships.items():
                if inspect.isfunction(rel):
                    rel_col = getattr(table.c, relationship_fks[rel_name])
                    properties[rel_name] = rel([rel_col])
                else:
                    properties[rel_name] = rel

            def __init__(self, **kw):
                self.__dict__.update(kw)
            Model = type(name, (object,), {'__init__': __init__})
            mapper(Model, table, properties=properties)
        metadata.create_all(engine)
        return Model
    return _make_model


@pytest.fixture
def form_factory(DBSession):
    """A factory function to create a form. The following arguments are
    accepted:

    * fields: A dictionary mapping attribute/field names to WTForms fields,
              defaults to an empty set of fields.
    * base: A base class to use, either this or bases is required.
    * bases: A tuple of base classes, can be specified if more than one base is
             desired.
    * name: An optional name, defaults to "SubForm"
    * model: The model to be used for the form. May be none, but  should
             normally be specified. If it is given, it is used as the "model"
             attribute of the "Meta" class.
    """
    @classmethod
    def get_dbsession(cls):
        return DBSession

    def make_form(fields=None, base=None, name='SubForm',
                  model=None, bases=None):
        if fields is None:
            fields = {}
        if base is None and bases is None:
            raise ValueError("Must have a base class")
        if base is not None and bases is not None:
            raise ValueError("Ambigous base classes")
        if bases is None:
            bases = (base,)

        fields['get_dbsession'] = get_dbsession
        if model is not None:
            fields['Meta'] = type('Meta', (object,), {'model': model})
        return type(name, bases, fields)
    return make_form


@pytest.fixture
def Model_one_pk(model_factory):
    return model_factory()


@pytest.fixture
def Model_two_pk(model_factory):
    cols = [Column('id2', Integer, primary_key=True)]
    return model_factory(cols)


@pytest.fixture
def Model_diff_colname(model_factory):
    return model_factory(defaults=[Column('id2', Integer, primary_key=True)],
                         col_name_to_attr_map={'id2': 'id'})


@pytest.fixture
def Model2_basic(model_factory):
    return model_factory(name='Model2')


@pytest.fixture
def Model2_many_to_one(model_factory, Model_one_pk):
    cols = [Column('model_id', ForeignKey('model.id'))]
    relationships = {
        'model': relationship(Model_one_pk, backref='models')
    }
    return model_factory(cols, 'Model2', relationships=relationships)


@pytest.fixture
def Model2_many_to_one_multiple(model_factory, Model_one_pk):
    cols = [Column('model_id1', ForeignKey('model.id')),
            Column('model_id2', ForeignKey('model.id'))]
    relationships = {
        'model1': lambda fks: relationship(Model_one_pk, backref='models1',
                                           foreign_keys=fks),
        'model2': lambda fks: relationship(Model_one_pk, backref='models2',
                                           foreign_keys=fks),
    }
    relationship_fks = {
        'model1': 'model_id1',
        'model2': 'model_id2',
    }
    return model_factory(cols, 'Model2', relationships=relationships,
                         relationship_fks=relationship_fks)
