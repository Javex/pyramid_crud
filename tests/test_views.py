from pyramid.httpexceptions import HTTPFound
from pyramid_crud.views import CRUDView
from pyramid_crud import forms
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from webob.multidict import MultiDict
try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch
import pytest

# TODO: Test with multiple PK


@pytest.fixture
def route_setup(config):
    basename = 'tests.test_views.MyView.'
    config.add_route(basename + "list", '/test')
    config.add_route(basename + "edit", '/test/{id}')
    config.add_route(basename + "delete", '/test/delete/{id}')
    config.add_route(basename + "new", '/test/new')
    config.commit()


@pytest.fixture
def csrf_token(session, pyramid_request):
    session.get_csrf_token.return_value = 'ABCD'
    token = pyramid_request.session.get_csrf_token()
    pyramid_request.POST['csrf_token'] = token


class TestCRUDView(object):

    @pytest.fixture(autouse=True)
    def _prepare_view(self, pyramid_request, DBSession, form_factory,
                      model_factory):
        self.request = pyramid_request
        self.request.POST = MultiDict(self.request.POST)
        self.Model = model_factory([Column('test_text', String),
                                    Column('test_bool', Boolean)])
        self.Model.test_text.info["label"] = "Test Text"
        self.Model.test_bool.info["label"] = "Test Bool"
        self.Model.id.info["label"] = "ID"
        self.Model.__str__ = lambda self: 'ModelStr'
        self.Form = form_factory(model=self.Model, base=forms.CSRFModelForm)
        self.request.dbsession = DBSession
        self.session = DBSession

        class MyView(CRUDView):
            Form = self.Form
            url_path = '/test'
        self.View = MyView
        self.view = self.View(self.request)

    @pytest.fixture
    def obj(self):
        obj = self.Model(test_text='test', test_bool=True)
        self.session.add(obj)
        self.session.flush()
        assert obj.id
        return obj

    @pytest.fixture
    def ChildForm(self, model_factory, form_factory):
        cols = [Column('id', Integer, primary_key=True),
                Column('parent_id', ForeignKey('model.id')),
                ]
        rels = {'parent': relationship(self.Model, backref='children')}
        ChildModel = model_factory(cols, 'Child', relationships=rels)
        ChildForm = form_factory(model=ChildModel, base=forms.CSRFModelForm)
        return ChildForm

    def test_title(self):
        assert self.view.title == "Model"

    def test_title_plural(self):
        assert self.view.title_plural == "Models"

    def test_list_display(self):
        [default] = self.view.list_display
        assert default == '__str__'

    def test_iter_head_cols_default(self):
        [col] = list(self.view.iter_head_cols())
        assert col == {'label': 'Model', 'css_class': 'column-Model'}

    def test_iter_head_cols_model_attr(self):
        self.View.list_display = ('id', 'test_text', 'test_bool')
        cols = list(self.view.iter_head_cols())
        assert cols == [{'label': 'ID', 'css_class': 'column-id'},
                        {'label': 'Test Text',
                         'css_class': 'column-test_text'},
                        {'label': 'Test Bool', 'css_class': 'column-test_bool',
                         'bool': True}]

    def test_iter_head_cols_model_callable(self):
        def meth(self):
            pass
        meth.info = {'label': 'Test Text Lower'}
        self.Model.test_text_lower = meth
        self.View.list_display = ('test_text_lower',)
        cols = list(self.view.iter_head_cols())
        assert cols == [{'label': 'Test Text Lower',
                         'css_class': 'column-test_text_lower'}]

    def test_iter_head_cols_generic_callable(self):
        def meth(obj):
            pass
        meth.info = {'label': 'Test Foo'}
        self.View.meth = meth
        self.View.list_display = (meth,)
        cols = list(self.view.iter_head_cols())
        assert cols == [{'label': 'Test Foo', 'css_class': 'column-meth'}]

    def test_iter_head_cols_view_callable(self):
        def foo(self, obj):
            pass
        foo.info = {'label': 'Foo'}
        self.View.foo = foo
        self.View.list_display = ('foo',)
        cols = list(self.view.iter_head_cols())
        assert cols == [{'label': 'Foo', 'css_class': 'column-foo'}]

    def test_iter_head_cols_custom_class(self):
        def foo(self, obj):
            pass
        foo.info = {'label': 'Foo', 'css_class': 'foofoo'}
        self.View.foo = foo
        self.View.list_display = ('foo',)
        cols = list(self.view.iter_head_cols())
        assert cols == [{'label': 'Foo', 'css_class': 'foofoo'}]

    def test_iter_head_cols_missing_info_callable(self):
        def foo_test(self, obj):
            pass
        self.View.foo = foo_test
        self.View.list_display = (foo_test,)
        cols = list(self.view.iter_head_cols())
        assert cols == [{'label': 'Foo Test', 'css_class': 'column-foo_test'}]

    def test_iter_head_cols_missing_info_attr(self):
        delattr(self.Model.test_text, 'info')
        self.View.list_display = ('test_text',)
        cols = list(self.view.iter_head_cols())
        assert cols == [{'label': 'Test Text',
                         'css_class': 'column-test_text'}]

    def test_iter_head_cols_wrong_attr(self):
        self.View.list_display = ('doesnotexist',)
        with pytest.raises(AttributeError):
            list(self.view.iter_head_cols())

    def test_iter_list_cols_default(self, obj):
        cols = list(self.view.iter_list_cols(obj))
        assert cols == ['ModelStr']

    def test_iter_list_cols_model_attr(self, obj):
        self.View.list_display = ('id', 'test_text', 'test_bool')
        cols = list(self.view.iter_list_cols(obj))
        assert cols == [1, 'test', True]

    def test_iter_list_cols_model_callable(self, obj):
        def meth(self):
            return self.test_text.upper()
        self.Model.test_text_upper = meth
        self.View.list_display = ('test_text_upper',)
        cols = list(self.view.iter_list_cols(obj))
        assert cols == ['TEST']

    def test_iter_list_cols_generic_callable(self, obj):
        def meth(obj):
            return obj.test_text.upper()
        self.View.list_display = (meth,)
        cols = list(self.view.iter_list_cols(obj))
        assert cols == ['TEST']

    def test_iter_list_cols_view_callable(self, obj):
        def upper(self, obj):
            return obj.test_text.upper()
        self.View.upper = upper
        self.View.list_display = ('upper',)
        cols = list(self.view.iter_list_cols(obj))
        assert cols == ['TEST']

    def test_template_dir(self):
        assert self.view.template_dir == 'default'

    def test_template_ext(self):
        assert self.view.template_ext == '.mako'

    def test_template_base_name(self):
        assert self.view.template_base_name == 'base'

    def test_button_form(self):
        assert self.view.button_form is forms.ButtonForm

    def test_delete_form_factory(self):
        form = self.view.delete_form_factory(self.request.POST,
                                             csrf_context=self.request)
        assert isinstance(form, forms.ButtonForm)

    def test_delete_form(self):
        assert self.view._delete_form is None
        assert isinstance(self.view.delete_form(), forms.ButtonForm)
        assert isinstance(self.view._delete_form, forms.ButtonForm)

    def test__template_for(self):
        self.View.foo_template = "sometemplate.mako"
        assert self.View._template_for("foo") == "sometemplate.mako"

    def test__template_for_default(self):
        assert self.View._template_for("foo") == "default/foo.mako"

    @pytest.mark.usefixtures("route_setup")
    def test_redirect(self):
        redirect = self.view.redirect("tests.test_views.MyView.list")
        assert isinstance(redirect, HTTPFound)
        assert redirect.location == 'http://example.com/test'

    @pytest.mark.usefixtures("route_setup")
    def test_redirect_default(self):
        self.request.matched_route = MagicMock()
        self.request.matched_route.name = 'tests.test_views.MyView.list'
        redirect = self.view.redirect()
        assert isinstance(redirect, HTTPFound)
        assert redirect.location == 'http://example.com/test'

    def test_route_name(self):
        assert self.View.route_name("test") == "tests.test_views.MyView.test"

    def test__get_route_pks(self, obj):
        assert self.view._get_route_pks(obj) == {'id': obj.id}

    def test__get_route_pks_empty_id(self):
        obj = self.Model()
        with pytest.raises(ValueError):
            self.view._get_route_pks(obj)

    @pytest.mark.usefixtures("route_setup")
    def test__delete_route(self, obj):
        route = self.view._delete_route(obj)
        assert route == "http://example.com/test/delete/%d" % obj.id

    @pytest.mark.usefixtures("route_setup")
    def test__edit_route(self, obj):
        route = self.view._edit_route(obj)
        assert route == "http://example.com/test/%d" % obj.id

    def test__get_request_pks(self):
        self.request.matchdict['id'] = 4
        assert self.view._get_request_pks() == {'id': 4}

    def test__get_request_pks_empty(self):
        assert self.view._get_request_pks() is None

    def test__get_request_pks_half_empty(self):
        self.request.matchdict['id'] = 4
        with patch('pyramid_crud.views.get_pks') as mock:
            mock.return_value = ['id', 'id2']
            with pytest.raises(ValueError):
                self.view._get_request_pks()
            assert mock.call_count == 1

    def test_list_empty(self):
        data = self.view.list()
        assert len(data) == 1
        query = data['items']
        assert list(query) == []

    def test_list_obj(self, obj):
        data = self.view.list()
        assert len(data) == 1
        query = data['items']
        items = list(query)
        assert len(items) == 1
        item = items[0]
        assert item == obj

    @pytest.mark.usefixtures("route_setup", "csrf_token")
    def test_delete(self, obj):
        self.request.method = 'POST'
        self.request.matchdict['id'] = obj.id
        redirect = self.view.delete()
        assert isinstance(redirect, HTTPFound)
        flash = self.request.session.flash
        flash.assert_called_once_with('Model deleted!')

    def test_delete_wrong_method(self):
        self.request.method = 'GET'
        with pytest.raises(AssertionError):
            self.view.delete()

    @pytest.mark.usefixtures("route_setup", "csrf_token")
    def test_delete_not_found(self):
        self.request.method = 'POST'
        self.request.matchdict['id'] = 1
        with pytest.raises(HTTPFound):
            self.view.delete()
        flash = self.request.session.flash
        flash.assert_called_once_with('Model not found!', 'error')

    @pytest.mark.usefixtures("route_setup", "session")
    def test_delete_missing_pks(self):
        self.request.method = 'POST'
        with pytest.raises(HTTPFound):
            self.view.delete()
        flash = self.request.session.flash
        flash.assert_called_once_with('Invalid URL', 'error')

    @pytest.mark.usefixtures("csrf_token", "route_setup")
    def test_delete_wrong_token(self):
        self.request.method = 'POST'
        self.request.matchdict['id'] = 1
        self.request.POST['csrf_token'] = 'WRONG'
        with pytest.raises(HTTPFound):
            self.view.delete()
        flash = self.request.session.flash
        flash.assert_called_once_with('Delete failed.', 'error')

    @pytest.mark.usefixtures("csrf_token")
    @pytest.mark.parametrize("is_new", [True, False])
    def test_edit_GET(self, obj, is_new):
        self.request.POST = MultiDict()
        if not is_new:
            self.request.matchdict['id'] = obj.id
        params = self.view.edit()
        assert self.request.session.flash.call_count == 0
        assert len(params) == 2
        assert params['is_new'] is is_new
        form = params['form']
        assert len(list(form))
        if not is_new:
            assert form.test_text.data == 'test'
        else:
            assert not form.test_text.data

    @pytest.mark.usefixtures("route_setup", "session")
    def test_edit_request_pks_exc(self):
        exc_mock = MagicMock(side_effect=ValueError("Either all primary keys "
                                                    "have to be set or None"))
        self.view._get_request_pks = exc_mock
        with pytest.raises(HTTPFound):
            self.view.edit()
        exc_mock.assert_called_once_with()
        flash = self.request.session.flash
        flash.assert_called_once_with('Invalid URL', 'error')

    @pytest.fixture(params=['edit', 'new'])
    def edit_run_factory(self, obj, csrf_token, route_setup, request):
        """
        Runs an edit with a given action.
        """
        def run(action, test_text='testval', expect_redirect=True):
            self.request.method = 'POST'
            if request.param == 'edit':
                self.request.matchdict['id'] = obj.id
            self.request.POST['test_text'] = test_text
            self.request.POST[action] = "Foo"
            # either redirect or retparams
            retval = self.view.edit()
            flash = self.request.session.flash
            if expect_redirect:
                assert flash.call_count == 1
                args, kw = flash.call_args
                assert len(args) == 1
                assert len(kw) == 0
                if request.param == 'edit':
                    assert "edited" in args[0]
                    new_obj = obj
                else:
                    assert "added" in args[0]
                    # We have a new object
                    new_obj = (self.session.query(self.Model).
                               filter(self.Model.id != obj.id).one())
                assert new_obj.test_text == test_text
                assert isinstance(retval, HTTPFound)
                return retval.location, new_obj
            else:
                is_new = request.param == 'new'
                return retval, is_new
        return run

    def test_edit_save(self, edit_run_factory):
        location, obj = edit_run_factory('save')
        assert location == 'http://example.com/test/%d' % obj.id

    def test_edit_save_no_value(self, obj, edit_run_factory):
        obj.test_text = 'Foo'
        location, obj = edit_run_factory('save', None)
        assert location == 'http://example.com/test/%d' % obj.id

    def test_edit_save_new(self, edit_run_factory):
        location, _ = edit_run_factory('save_new')
        assert location == 'http://example.com/test/new'

    def test_edit_save_close(self, edit_run_factory):
        location, _ = edit_run_factory('save_close')
        assert location == 'http://example.com/test'

    def test_edit_invalid_action(self, edit_run_factory):
        self.request.method = 'POST'
        with pytest.raises(ValueError):
            edit_run_factory('invalid_action')

    def test_edit_invalid_form(self, edit_run_factory):
        del self.request.POST['csrf_token']
        params, is_new = edit_run_factory('save', expect_redirect=False)
        assert len(params) == 2
        assert params['is_new'] is is_new
        form = params['form']
        assert len(form.errors) == 1
        assert form.csrf_token.errors

    def test_edit_add_item(self, edit_run_factory):
        params, is_new = edit_run_factory('add_foo', expect_redirect=False)
        assert len(params) == 2
        assert params['is_new'] is is_new
        form = params['form']
        assert len(form.errors) == 0
        assert self.request.session.flash.call_count == 0


class TestCrudCreator(object):

    @pytest.fixture(autouse=True)
    def _prepare_view(self, pyramid_request, DBSession, form_factory,
                      model_factory):
        self.Model = model_factory([Column('test_text', String)])
        self.Form = form_factory(model=self.Model, base=forms.CSRFModelForm)

        def make_view(**kwargs):
            return type('MyView', (CRUDView,), kwargs)
        self.make_view = make_view

    def test_okay_config(self):
        View = self.make_view(Form=self.Form, url_path='/test')
        assert View.Form is self.Form
        assert View.url_path == "/test"
        assert hasattr(View, '__venusian_callbacks__')

    def test_missing_form(self):
        with pytest.raises(AttributeError):
            self.make_view(url_path='/test')

    def test_missing_url_path(self):
        with pytest.raises(AttributeError):
            self.make_view(Form=self.Form)

    def test_missing_all(self):
        with pytest.raises(AttributeError):
            self.make_view()

    def test_abstract(self):
        View = self.make_view(__abstract__=True)
        assert not hasattr(View, '__venusian_callbacks__')

    def test_route_setup(self):
        View = self.make_view(Form=self.Form, url_path='/test')
        cb = list(View.__venusian_callbacks__.values())[0][0][0]
        context = MagicMock()
        cb(context, None, None)
        config = context.config.with_package()
        routes = [('tests.test_views.MyView.list', '/test'),
                  ('tests.test_views.MyView.new', '/test/new'),
                  ('tests.test_views.MyView.edit', '/test/{id}'),
                  ('tests.test_views.MyView.delete', '/test/{id}/delete')]
        views = [((View,),
                  {'attr': 'list',
                   'route_name': 'tests.test_views.MyView.list',
                   'renderer': 'default/list.mako',
                   'request_method': 'GET'}),
                 ((View,),
                  {'attr': 'edit',
                   'route_name': 'tests.test_views.MyView.edit',
                   'renderer': 'default/edit.mako'}),
                 ((View,),
                  {'attr': 'edit',
                   'route_name': 'tests.test_views.MyView.new',
                   'renderer': 'default/edit.mako'}),
                 ((View,),
                  {'attr': 'delete',
                   'route_name': 'tests.test_views.MyView.delete',
                   'request_method': 'POST'}),
                 ]
        assert config.add_route.call_count == 4
        assert config.add_view.call_count == 4
        for route, view in zip(routes, views):
            assert (route, {}) in config.add_route.call_args_list
            assert view in config.add_view.call_args_list
