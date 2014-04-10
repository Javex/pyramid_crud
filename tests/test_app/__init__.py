from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from sqlalchemy import create_engine

from .models import DBSession, Base


def main(**settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = create_engine('sqlite://')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all()
    session_factory = UnencryptedCookieSessionFactoryConfig('itsaseekreet')
    config = Configurator(settings=settings,
                          session_factory=session_factory)
    config.include('pyramid_mako')
    config.include('pyramid_crud')
    config.scan()
    return config.make_wsgi_app()
