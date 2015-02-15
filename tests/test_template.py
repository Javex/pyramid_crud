import pytest
from pyramid.renderers import render as pyramid_render
from pyramid_crud import forms, views
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from webob.multidict import MultiDict
from pyramid.interfaces import IRendererFactory
from wtforms.fields import HiddenField, TextAreaField
from bs4 import BeautifulSoup
import re

themes = ['pyramid_crud:templates/mako/bootstrap']

pytestmark = pytest.mark.usefixtures("template_setup")

err_required = re.compile(r'<ul>\s*<li>This field is required.</li>\s*</ul>')


def render_factory(template_name, request, **additional_args):
    def render(**kw):
        additional_args.update(kw)
        out = pyramid_render(template_name, additional_args, request=request)
        return BeautifulSoup(out)
    return render


@pytest.fixture(params=themes)
def theme(request):
    return request.param


@pytest.fixture(params=['horizontal', 'grid'])
def edit_template(request):
    return request.param


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
    fieldsets = [{'title': 'Bar', 'fields': ['test_text', 'test_bool']}]
    _Form = form_factory(model=Model, base=forms.CSRFModelForm,
                         fields={'fieldsets': fieldsets})

    class MyView(views.CRUDView):
        Form = _Form
        url_path = '/test'
        list_display = ('id', 'test_text', 'test_bool')
    venusian_init(MyView)
    view = MyView(pyramid_request)
    config.commit()
    return view


@pytest.fixture
def render_base(pyramid_request, config, theme):
    # For base we need an inheriting template to avoid recursion
    tmpl = """<%inherit file="${context.get('theme')}/base.mako"/>
    <%block name="head">HeadTest</%block>
    <%block name="heading">HeadingTest</%block>
    Test Body"""
    renderer = config.registry.queryUtility(IRendererFactory, '.mako')
    renderer.lookup.put_string('test.mako', tmpl)
    return render_factory("test.mako", pyramid_request, theme=theme)


@pytest.fixture
def render_list(pyramid_request, theme):
    return render_factory("%s/list.mako" % theme, pyramid_request)


@pytest.fixture
def render_edit(pyramid_request, theme):
    return render_factory("%s/edit.mako" % theme, pyramid_request)


def test_base(render_base, view):
    out = render_base(view=view)
    assert "<title>Models | CRUD</title>" in str(out)
    assert "Test Body" in str(out)
    assert "HeadingTest" in str(out)
    assert "HeadTest" in str(out)


@pytest.mark.parametrize("queue, class_", [('error', 'danger'),
                                           ('warning', 'warning'),
                                           ('info', 'info'),
                                           (None, 'success')])
def test_base_flash_msg(queue, class_, render_base, session, view):
    session.pop_flash.return_value = ["Test Message"]
    out = render_base(view=view)
    assert "alert-%s" % class_ in str(out)
    assert "Test Message" in str(out)
    assert session.pop_flash.called_once_with(queue)


def test_list(render_list, view):
    obj = view.Form.Meta.model(test_text='Testval', test_bool=True)
    view.dbsession.add(obj)
    out = render_list(view=view, **view.list())
    assert "Testval" in str(out)
    heads = out.find_all("th")
    text_head = heads[2]
    bool_head = heads[3]
    assert 'column-test_text' in text_head.attrs['class']
    assert 'column-test_bool' in bool_head.attrs['class']
    assert 'Test Text' in text_head.string.strip()
    assert 'Test Bool' in bool_head.string.strip()
    assert "<h1>Models</h1>" == str(out.find("h1"))
    assert "Models | CRUD" == out.find("title").string.strip()
    bool_item = out.find_all('td')[3]
    assert 'text-success' in bool_item.attrs['class']
    assert 'Yes' == bool_item.string.strip()
    assert out.find("input", attrs={'name': 'csrf_token', 'type': 'hidden'})


def test_list_bool_false(render_list, view):
    obj = view.Form.Meta.model(test_bool=False, test_text='Foo')
    view.dbsession.add(obj)
    out = render_list(view=view, **view.list())
    bool_item = out.find_all('td')[3]
    assert 'text-danger' in bool_item.attrs['class']
    assert 'No' == bool_item.string.strip()


def test_list_bool_false_link(render_list, view):
    view.list_display_links = ['test_bool']
    obj = view.Form.Meta.model(test_bool=False, test_text='Foo')
    view.dbsession.add(obj)
    out = render_list(view=view, **view.list())
    bool_item = out.find_all('td')[3]
    assert 'text-danger' in bool_item.attrs['class']
    bool_a = bool_item.find('a')
    assert bool_a.string.strip() == 'No'


# TODO: Implement a test for when no items exist yet (and add that
# functionality)
def test_list_empty():
    pass


def test_edit(render_edit, view, edit_template):
    view.Form.fieldsets[0]["template"] = edit_template
    obj = view.Form.Meta.model(test_text='Testval', test_bool=True)
    view.dbsession.add(obj)
    view.dbsession.flush()
    view.request.matchdict["id"] = obj.id
    out = render_edit(view=view, **view.edit())
    assert "Edit Model" == out.find("h1").string.strip()
    # Fieldset not present!
    assert "Add another" not in str(out)
    assert out.find("input", attrs={'name': 'csrf_token', 'type': 'hidden'})
    text_field = out.find('input', attrs={'name': 'test_text'})
    text_label = out.find('label', attrs={'for': 'test_text'})
    assert text_field.attrs["value"] == "Testval"
    assert "required" in text_field.attrs
    assert text_label.string.strip() == "Test Text"
    bool_field = out.find('input', attrs={'name': 'test_bool'})
    bool_label = out.find('label', attrs={'for': 'test_bool'})
    assert bool_field.attrs['value'] == "y"
    assert bool_label.string.strip() == "Test Bool"
    assert "This field is required." not in str(out)


def test_edit_fieldset_title(render_edit, view, edit_template):
    view.Form.fieldsets = [{'title': 'Foo', 'fields': [],
                            'template': edit_template}]
    out = render_edit(view=view, **view.edit())
    assert out.find("legend").string.strip() == "Foo"
    assert "test_text" not in str(out)
    assert "test_bool" not in str(out)


def test_edit_hidden_field(render_edit, view, form_factory):
    Form = form_factory({'hid_field': HiddenField(), 'area': TextAreaField()},
                        base=forms.CSRFModelForm,
                        model=view.Form.Meta.model)
    view.__class__.Form = Form
    out = render_edit(view=view, **view.edit())
    assert out.find("input", attrs={'name': 'hid_field', 'type': 'hidden'})
    assert out.find("textarea", attrs={'name': 'area'})


def test_edit_new(render_edit, view, edit_template):
    view.Form.fieldsets[0]["template"] = edit_template
    out = render_edit(view=view, **view.edit())
    assert out.find("h1").string.strip() == "New Model"
    assert "Add another" not in str(out)
    assert out.find("input", attrs={'name': 'csrf_token', 'type': 'hidden'})
    text_field = out.find("input", attrs={'name': 'test_text'})
    text_label = out.find("label", attrs={'for': 'test_text'})
    assert text_label.string.strip() == "Test Text"
    assert text_field.attrs["value"] == ""
    assert "required" in text_field.attrs

    bool_field = out.find("input", attrs={'name': 'test_bool',
                                          'type': 'checkbox'})
    bool_label = out.find("label", attrs={'for': 'test_bool'})
    assert bool_label.string.strip() == "Test Bool"
    assert bool_field.attrs["value"] == "y"
    assert "This field is required." not in out


def test_edit_field_errors(render_edit, view, edit_template):
    view.Form.fieldsets[0]["template"] = edit_template
    view.request.method = 'POST'
    view.request.POST["save"] = "Foo"
    out = render_edit(view=view, **view.edit())
    err_msg = str(out.find("div", class_='alert-danger'))
    assert "This field is required." in err_msg


# TODO: These checks should do something
def check_grid(out, view):
    pass


def check_horizontal(out, view):
    pass


@pytest.mark.parametrize("template, check_template",
                         [('horizontal', check_horizontal),
                          ('grid', check_grid),
                          ])
def test_edit_template(render_edit, view, template, check_template):
    view.Form.fieldsets[0]['template'] = template
    out = render_edit(view=view, **view.edit())
    check_template(out, view)
    assert out.find("legend").string.strip() == "Bar"


@pytest.mark.parametrize("with_obj", [True, False])
def test_edit_inline_tabular(render_edit, view, model_factory, form_factory,
                             with_obj, edit_template):
    view.Form.fieldsets[0]["template"] = edit_template
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
        parent.children.append(ChildModel())
        view.dbsession.add(parent)
        view.dbsession.flush()
        view.request.matchdict["id"] = parent.id
    out = render_edit(view=view, **view.edit())
    assert out.find_all("legend")[1].string.strip() == "Childs"
    text_head, delete_head = out.find_all("th")
    assert text_head.string.strip() == "child_text"
    assert delete_head.string.strip() == "Delete?"
    assert out.find("input", attrs={'name': 'child_0_child_text'})
    assert out.find("input", attrs={'name': 'delete_child_0'})
    assert out.find("input", attrs={'name': 'add_child'})
    if with_obj:
        child_id = out.find('input', attrs={'name': 'child_0_id'})
        assert child_id.attrs['value'] == '1'
        child_id = out.find('input', attrs={'name': 'child_1_id'})
        assert child_id.attrs['value'] == '2'
    else:
        assert not re.search(r'child_\d+_id', str(out))


def test_list_display_links(render_list, view, edit_template):
    view.Form.fieldsets[0]["template"] = edit_template
    obj = view.Form.Meta.model(test_text='Testval', test_bool=True)
    view.request.dbsession.add(obj)
    view.request.dbsession.flush()
    view.__class__.list_display_links = ('test_text', 'test_bool')
    out = render_list(view=view, **view.list())
    _, _, text_cell, bool_cell = out.find_all("td")
    assert text_cell.find("a").string.strip() == "Testval"
    assert bool_cell.find("a").string.strip() == "Yes"
