import os

__version__ = '0.1.2'


def includeme(config):
    here = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(here, 'templates')
    config.add_settings({'mako.directories': template_dir})
    # TODO: Add setting for which static path to use and add that static path
    # using config.add_static_view
    raise NotImplementedError("Check for existing session!")
