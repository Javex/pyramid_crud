import pytest
from pyramid.renderers import render as pyramid_render
from pyramid_crud import forms, views
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from webob.multidict import MultiDict
from pyramid.interfaces import IRendererFactory
from wtforms.fields import HiddenField
import re


pytestmark = pytest.mark.usefixtures("template_setup")
bool_head = re.compile(r'<th class="column-test_bool">\s+Test Bool\s+</th>')
bool_item_yes = re.compile(r'<td class="text-success text-center">\s*Yes\s*'
                           '</td>')
bool_item_no = re.compile(r'<td class="text-danger text-center">\s*No\s*'
                          '</td>')
bool_item_no_href = re.compile(
    r'<td class="text-danger text-center">\s*<a.*\s*No\s*</a>\s*</td>')
text_head = re.compile(r'<th class="column-test_text">\s+Test Text\s+</th>')
err_required = re.compile(r'<ul>\s*<li>This field is required.</li>\s*</ul>')


def render_factory(template_name, request):
    def render(**kw):
        return pyramid_render(template_name, kw, request=request)
    return render


@pytest.fixture
def view(pyramid_request, model_factory, form_factory, venusian_init, config,
         DBSession):
    config.add_static_view('/static/crud', 'pyramid_crud:static')
    pyramid_request.POST = MultiDict()
    pyramid_request.dbsession = DBSession
    Model = model_factory([Column('test_text', String, nullable=False),
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
def render_base(pyramid_request, config):
    # For base we need an inheriting template to avoid recursion
    tmpl = """<%inherit file="default/base.mako"/>
    <%block name="head">HeadTest</%block>
    <%block name="heading">HeadingTest</%block>
    Test Body"""
    renderer = config.registry.queryUtility(IRendererFactory, '.mako')
    renderer.lookup.put_string('test.mako', tmpl)
    return render_factory("test.mako", pyramid_request)


@pytest.fixture
def render_list(pyramid_request):
    return render_factory("default/list.mako", pyramid_request)


@pytest.fixture
def render_edit(pyramid_request):
    return render_factory("default/edit.mako", pyramid_request)


def test_base(render_base, view):
    out = render_base(view=view)
    assert "<title>Models | CRUD</title>" in out
    assert "Test Body" in out
    assert "HeadingTest" in out
    assert "HeadTest" in out


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


def test_list(render_list, view):
    obj = view.Form.Meta.model(test_text='Testval', test_bool=True)
    view.dbsession.add(obj)
    out = render_list(view=view, **view.list())
    assert "Testval" in out
    assert bool_head.search(out)
    assert text_head.search(out)
    assert "<h1>Models</h1>" in out
    assert "Models | CRUD" in out
    assert bool_item_yes.search(out)
    assert "Delete" in out
    assert "csrf_token" in out


def test_list_bool_false(render_list, view):
    obj = view.Form.Meta.model(test_bool=False, test_text='Foo')
    view.dbsession.add(obj)
    out = render_list(view=view, **view.list())
    assert bool_item_no.search(out)


def test_list_bool_false_link(render_list, view):
    view.list_display_links = ['test_bool']
    obj = view.Form.Meta.model(test_bool=False, test_text='Foo')
    view.dbsession.add(obj)
    out = render_list(view=view, **view.list())
    assert bool_item_no_href.search(out)


# TODO: Implement a test for when no items exist yet (and add that
# functionality)
def test_list_empty():
    pass


def test_edit(render_edit, view):
    obj = view.Form.Meta.model(test_text='Testval', test_bool=True)
    view.dbsession.add(obj)
    view.dbsession.flush()
    view.request.matchdict["id"] = obj.id
    out = render_edit(view=view, **view.edit())
    assert "<h1>Edit Model</h1>" in out
    # Fieldset not present!
    assert "Add another" not in out
    assert "csrf_token" in out
    assert 'name="test_text"' in out
    text = ('<label for="test_text">Test Text</label>: <input id="test_t'
            'ext" name="test_text" required type="text" value="Testval">')
    assert text in out
    bool_ = ('<label for="test_bool">Test Bool</label>: <input checked id'
             '="test_bool" name="test_bool" type="checkbox" value="y">')
    assert bool_ in out
    assert not err_required.search(out)


def test_edit_fieldset_title(render_edit, view):
    view.Form.fieldsets = [{'title': 'Foo', 'fields': []}]
    out = render_edit(view=view, **view.edit())
    assert "<legend>Foo</legend>" in out
    assert "test_text" not in out
    assert "test_bool" not in out


def test_edit_hidden_field(render_edit, view, form_factory):
    Form = form_factory({'hid_field': HiddenField()}, base=forms.CSRFModelForm,
                        model=view.Form.Meta.model)
    view.__class__.Form = Form
    out = render_edit(view=view, **view.edit())
    assert 'name="hid_field" type="hidden"' in out


def test_edit_new(render_edit, view):
    out = render_edit(view=view, **view.edit())
    assert "<h1>New Model</h1>" in out
    assert "Add another" not in out
    assert "csrf_token" in out
    assert 'name="test_text"' in out
    empty_text = ('<label for="test_text">Test Text</label>: <input id="test_t'
                  'ext" name="test_text" required type="text" value="">')
    assert empty_text in out
    empty_bool = ('<label for="test_bool">Test Bool</label>: <input id="test_b'
                  'ool" name="test_bool" type="checkbox" value="y">')
    assert empty_bool in out
    assert not err_required.search(out)


def test_edit_field_errors(render_edit, view):
    view.request.method = 'POST'
    view.request.POST["save"] = "Foo"
    out = render_edit(view=view, **view.edit())
    assert err_required.search(out)


@pytest.mark.parametrize("with_obj", [True, False])
def test_edit_inline_tabular(render_edit, view, model_factory, form_factory,
                             with_obj):
    cols = [Column('parent_id', ForeignKey('model.id')),
            Column('child_text', String)]
    rels = {'parent': relationship(view.Form.Meta.model, backref="children")}
    ChildModel = model_factory(cols, 'Child', relationships=rels)
    ChildForm = form_factory(name='ChildForm', base=forms.TabularInLine,
                             model=ChildModel)
    ChildForm.extra = 1
    ChildForm.relationship_name = 'children'
    view.Form.inlines.append(ChildForm)

    if with_obj:
        parent = view.Form.Meta.model(test_text='Foo')
        parent.children.append(ChildModel())
        view.dbsession.add(parent)
        view.dbsession.flush()
        view.request.matchdict["id"] = parent.id
    out = render_edit(view=view, **view.edit())
    assert "Childs" in out
    assert "<th>child_text</th>" in out
    assert "<th>Delete?</th>" in out
    assert 'name="child_0_child_text"' in out
    assert 'name="delete_child_0"' in out
    assert 'name="add_child"' in out
    if with_obj:
        assert 'name="child_0_id" value="1"' in out
    else:
        assert not re.search(r'child_\d+_id', out)


def test_list_display_links(render_list, view):
    obj = view.Form.Meta.model(test_text='Testval', test_bool=True)
    view.request.dbsession.add(obj)
    view.request.dbsession.flush()
    view.__class__.list_display_links = ('test_text', 'test_bool')
    out = render_list(view=view, **view.list())
    search_re = r'<a href="http://example.com/test/1/edit">\s*%s\s*</a>'
    assert re.search(search_re % 'Testval', out)
    assert re.search(search_re % 'Yes', out)
