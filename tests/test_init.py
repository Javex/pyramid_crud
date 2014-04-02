import pyramid_crud
import pytest
from pyramid.exceptions import ConfigurationError
from pyramid.interfaces import ISessionFactory


@pytest.fixture
def mako_renderer(config, no_renderer):
    "Add mako renderer as configuration to settings."
    config.add_settings({'crud.template_renderer': 'mako'})


@pytest.fixture
def no_renderer(config):
    "Disable templates."
    config.add_settings({'crud.template_renderer': 'None'})


@pytest.fixture(params=['mako'])
def any_renderer(config, request):
    """Enable any renderer. Will use one of all available renderers in each
     iteration."""
    config.add_settings({'crud.template_renderer': request.param})


@pytest.fixture
def static_prefix(config):
    "Add a static URL prefix with the name '/testprefix'"
    config.add_settings({'crud.static_url_prefix': '/testprefix'})


@pytest.fixture
def custom_settings(no_renderer, static_prefix):
    "A fixture that uses custom settings."


@pytest.fixture
def session_factory(config):
    f = lambda: None
    config.registry.registerUtility(f, ISessionFactory)


def test_check_session_no_factory(config):
    with pytest.raises(ConfigurationError):
        pyramid_crud.check_session(config)


@pytest.mark.usefixtures("session_factory")
def test_check_session_factory(config):
    pyramid_crud.check_session(config)


@pytest.mark.usefixtures("custom_settings", "static_prefix")
def test_parse_options_from_settings(config):
    settings = config.get_settings()
    ref_settings = {'template_renderer': None,
                    'static_url_prefix': '/testprefix',
                    }
    settings = pyramid_crud.parse_options_from_settings(settings, 'crud.')
    assert settings == ref_settings


def test_parse_options_from_settings_defaults():
    settings = pyramid_crud.parse_options_from_settings({}, 'crud.')
    ref_settings = {'template_renderer': 'mako',
                    'static_url_prefix': '/static/crud',
                    }
    assert settings == ref_settings


def test_parse_options_from_settings_no_renderer():
    settings = {'crud.template_renderer': None}
    settings = pyramid_crud.parse_options_from_settings(settings, 'crud.')
    assert settings['template_renderer'] is None


def test_parse_options_from_settings_no_renderer_str():
    settings = {'crud.template_renderer': 'None'}
    settings = pyramid_crud.parse_options_from_settings(settings, 'crud.')
    assert settings['template_renderer'] is None


@pytest.mark.usefixtures("custom_settings")
def test_parse_options_from_settings_invalid_renderer():
    settings = {'crud.template_renderer': 'invalid'}
    with pytest.raises(ConfigurationError):
        pyramid_crud.parse_options_from_settings(settings, 'crud.')


@pytest.mark.usefixtures("custom_settings", "session_factory", "mako_renderer")
def test_includeme_mako(config):
    pyramid_crud.includeme(config)
    settings = config.get_settings()
    mako_dirs = settings['mako.directories']
    assert mako_dirs == ['pyramid_crud:templates']


@pytest.mark.usefixtures("custom_settings", "session_factory", "mako_renderer")
def test_includeme_mako_dirs_str(config):
    config.add_settings({'mako.directories': ''})
    pyramid_crud.includeme(config)
    settings = config.get_settings()
    assert settings['mako.directories'] == ['pyramid_crud:templates']


@pytest.mark.usefixtures("session_factory")
def test_includeme_no_template(config):
    config.add_settings({'crud.template_renderer': 'None'})
    pyramid_crud.includeme(config)
    settings = config.get_settings()
    assert 'mako.directories' not in settings


def test_includeme_no_session(config):
    pyramid_crud.includeme(config)
    with pytest.raises(ConfigurationError):
        config.commit()


def test_includeme_session_correct_order(config):
    def register():
        f = lambda: None
        config.registry.registerUtility(f, ISessionFactory)
    config.action(('pyramid_crud', 'session_test'), register)
    pyramid_crud.includeme(config)
    config.commit()


def test_includeme_session_wrong_order(config):
    def register():
        f = lambda: None
        config.registry.registerUtility(f, ISessionFactory)
    config.action(('pyramid_crud', 'session_test'), register, order=2)
    pyramid_crud.includeme(config)
    with pytest.raises(ConfigurationError):
        config.commit()


@pytest.mark.usefixtures("custom_settings", "session_factory", "any_renderer")
def test_includeme_static_view(config, pyramid_request):
    pyramid_crud.includeme(config)
    config.commit()
    url = pyramid_request.static_url('pyramid_crud:static/test.png')
    assert url == 'http://example.com/testprefix/test.png'


@pytest.mark.usefixtures("session_factory", "any_renderer")
def test_includeme_static_view_default(config, pyramid_request):
    pyramid_crud.includeme(config)
    config.commit()
    url = pyramid_request.static_url('pyramid_crud:static/test.png')
    assert url == 'http://example.com/static/crud/test.png'
