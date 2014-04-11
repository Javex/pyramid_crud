from pyramid.exceptions import ConfigurationError
from pyramid.compat import is_nonstr_iter
from pyramid.settings import aslist
from pyramid.interfaces import ISessionFactory

__version__ = '0.1.3'


def parse_options_from_settings(settings, settings_prefix):
    """Parse out options."""
    def sget(name, default=None):
        return settings.get(settings_prefix + name, default)

    static_url_prefix = sget('static_url_prefix', '/static/crud')
    if static_url_prefix == 'None':
        static_url_prefix = None

    return dict(
        static_url_prefix=static_url_prefix,
    )


def check_session(config):
    if config.registry.queryUtility(ISessionFactory) is None:
        raise ConfigurationError(
            "No session factory registered. You must register a session "
            "factory for this module to work")


def includeme(config):
    settings = config.get_settings()
    opts = parse_options_from_settings(settings, 'crud.')

    if opts['static_url_prefix'] is not None:
        config.add_static_view(opts['static_url_prefix'],
                               'pyramid_crud:static')

    # order=1 to be executed **after** session_factory register callback.
    config.action(('pyramid_crud', 'check_session'),
                  lambda: check_session(config), order=1)
