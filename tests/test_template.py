import pytest
from pyramid.renderers import render as pyramid_render, get_renderer
from pyramid_crud import forms, views
from sqlalchemy import Column, String, Boolean
from webob.multidict import MultiDict
import re


pytestmark = pytest.mark.usefixtures("template_setup")
bool_head = re.compile(r'<th class="column-test_bool">\s+Test Bool\s+</th>')
bool_item = re.compile(r'<td class="text-success text-center">\s*Yes\s*</td>')
text_head = re.compile(r'<th class="column-test_text">\s+Test Text\s+</th>')


def render_factory(template_name, request):
    def render(**kw):
        return pyramid_render(template_name, kw, request=request)
    return render


@pytest.fixture
def view(pyramid_request, model_factory, form_factory, venusian_init, config,
         DBSession):
    pyramid_request.POST = MultiDict()
    pyramid_request.dbsession = DBSession
    Model = model_factory([Column('test_text', String),
                           Column('test_bool', Boolean)])
    Model.test_text.info["label"] = "Test Text"
    Model.test_bool.info["label"] = "Test Bool"
    Model.id.info["label"] = "ID"

    def model_str(obj):
        return obj.test_text
    Model.__str__ = model_str
    _Form = form_factory(model=Model, base=forms.CSRFModelForm)

    class MyView(views.CRUDView):
        Form = _Form
        url_path = '/test'
        list_display = ('id', 'test_text', 'test_bool')
    view = MyView(pyramid_request)
    venusian_init(view)
    config.commit()
    return view


@pytest.fixture
def render_base(pyramid_request):
    # For base we need an inheriting template to avoid recursion
    tmpl = """<%inherit file="default/base.mako"/>Test Body"""
    renderer = get_renderer('test.mako', 'pyramid_crud')
    renderer.lookup.put_string('test.mako', tmpl)
    return render_factory("test.mako", pyramid_request)


@pytest.fixture
def render_list(pyramid_request):
    return render_factory("default/list.mako", pyramid_request)


def test_base(render_base, view):
    out = render_base(view=view)
    assert "<title>Models | CRUD</title>" in out
    assert "Test Body" in out


@pytest.mark.parametrize("queue, class_", [('error', 'danger'),
                                           ('warning', 'warning'),
                                           ('info', 'info'),
                                           (None, 'success')])
def test_base_flash_msg(queue, class_, render_base, session, view):
    session.pop_flash.return_value = ["Test Message"]
    out = render_base(view=view)
    assert "alert-%s" % class_ in out
    assert "Test Message" in out
    assert session.pop_flash.called_once_with(queue)


def test_list(render_list, view, config):
    obj = view.Form.Meta.model(test_text='Testval', test_bool=True)
    view.dbsession.add(obj)
    out = render_list(view=view, **view.list())
    assert "Testval" in out
    assert bool_head.search(out)
    assert text_head.search(out)
    assert "<h1>Models</h1>" in out
    assert "Models | CRUD" in out
    assert bool_item.search(out)
