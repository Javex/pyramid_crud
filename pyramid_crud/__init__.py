import os
from pyramid.exceptions import ConfigurationError
from pyramid.compat import is_nonstr_iter
from pyramid.settings import aslist
from pyramid.interfaces import ISessionFactory

__version__ = '0.1.3'


def parse_options_from_settings(settings, settings_prefix):
    """Parse out options."""
    def sget(name, default=None):
        return settings.get(settings_prefix + name, default)

    template_renderer = sget('template_renderer', 'mako')
    if template_renderer == 'None':
        template_renderer = None
    if template_renderer not in (None, 'mako'):
        raise ConfigurationError("Template Renderer '%s' is not supported"
                                 % template_renderer)

    static_url_prefix = sget('static_url_prefix', '/static/crud')

    return dict(
        template_renderer=template_renderer,
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

    if opts['template_renderer'] == 'mako':
        mako_dirs = settings.get('mako.directories', [])
        # Copied from pyramid_mako
        if not is_nonstr_iter(mako_dirs):
            # Since we parse a value that comes from an .ini config,
            # we treat whitespaces and newline characters equally as list item
            # separators.
            mako_dirs = aslist(mako_dirs, flatten=True)
        mako_dirs.append('pyramid_crud:templates')
        config.add_settings({'mako.directories': mako_dirs})

        # This option only makes sense when templates are in use
        config.add_static_view(opts['static_url_prefix'],
                               'pyramid_crud:static')
    else:
        pass

    # order=1 to be executed **after** session_factory register callback.
    config.action(('pyramid_crud', 'check_session'),
                  lambda: check_session(config), order=1)
