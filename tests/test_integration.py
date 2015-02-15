from pyramid import testing
from pyramid.session import UnencryptedCookieSessionFactoryConfig
import pytest
from pyramid_crud import forms, views
from webob.multidict import MultiDict


@pytest.fixture
def pyramid_request():
    r = testing.DummyRequest()
    r.POST = MultiDict()
    return r


@pytest.yield_fixture
def config():
    cfg = testing.setUp(autocommit=False)
    cfg.include('pyramid_mako')
    cfg.include('pyramid_crud')
    sess = UnencryptedCookieSessionFactoryConfig('itsaseekreet')
    cfg.set_session_factory(sess)
    cfg.commit()

    yield cfg

    testing.tearDown()


class TestMinimal(object):

    @pytest.fixture
    def minimal_model(self, model_factory):
        Model = model_factory()
        return Model

    @pytest.fixture
    def minimal_form(self, minimal_model):
        class MyForm(forms.CSRFModelForm):
            class Meta:
                model = minimal_model
        return MyForm

    @pytest.fixture
    def minimal_view(self, config, minimal_form, DBSession, pyramid_request):
        class MyView(views.CRUDView):
            Form = minimal_form
            url_path = '/items'
        pyramid_request.dbsession = DBSession
        return MyView

    @pytest.fixture(autouse=True)
    def _prepare(self, minimal_model, minimal_form, minimal_view):
        self.model = minimal_model
        self.form = minimal_form
        self.view = minimal_view

    def test_minimal_list(self, minimal_view, pyramid_request):
        result = minimal_view(pyramid_request).list()
        assert len(result) == 2
        assert 'action_form' in result
        assert result['items'].all() == []

    def test_minimal_list_items(self, minimal_view, pyramid_request, DBSession,
                                minimal_model):
        DBSession.add_all([minimal_model(), minimal_model()])
        DBSession.flush()
        result = minimal_view(pyramid_request).list()
        assert len(result) == 2
        assert 'action_form' in result
        items = result['items'].all()
        assert len(items) == 2
        for item in items:
            assert item.id

    def test_minimal_new(self, minimal_view, pyramid_request):
        result = minimal_view(pyramid_request).edit()
        assert len(result) == 2
        assert result['is_new']
        form = result['form']
        assert len(list(form)) == 1
        assert form.csrf_token

    def test_minimal_edit(self, minimal_view, pyramid_request, minimal_model,
                          DBSession):
        DBSession.add_all([minimal_model(), minimal_model()])
        DBSession.flush()
        pyramid_request.matchdict["id"] = 1
        result = minimal_view(pyramid_request).edit()
        assert len(result) == 2
        assert not result['is_new']
        form = result['form']
        assert len(list(form)) == 1
        assert form.csrf_token


class TestFunctional(object):

    @pytest.fixture(autouse=True)
    def _prepare(self):
        from .test_app import main
        from webtest import TestApp
        self.app = TestApp(main())

    def test_list_empty(self):
        response = self.app.get('/polls')
        assert response.status_int == 200
        assert "<title>Polls | CRUD</title>" in response
        tables = response.html.find_all("table")
        assert len(tables) == 1
        [table] = tables
        titles = ['Question', 'Date Published', 'Published?']
        for td, title in zip(table.find("thead").find("tr").find_all("td"),
                             titles):
            assert td.string == title
        rows = response.html.find("tbody").find_all("tr")
        assert len(rows) == 0

    def test_new_edit_delete(self):
        # Get a list of items
        response = self.app.get('/polls')
        assert response.status_int == 200

        # Fetch the form for a new item
        response = response.click(href="http://localhost/polls/new")
        assert response.status_int == 200
        assert len(response.forms) == 1
        # Make sure the extra fields are there
        assert 'choice_0_choice_text' in response.form.fields
        assert 'choice_1_choice_text' in response.form.fields
        assert 'choice_2_choice_text' not in response.form.fields

        # Remove the extra fields
        response = response.form.submit('delete_choice_0')
        assert response.status_int == 200
        response = response.form.submit('delete_choice_0')
        assert response.status_int == 200

        # Create an invalid form
        response = response.form.submit('save_close')
        assert response.status_int == 200
        assert "This field is required" in response

        # Fill out the form properly
        form = response.form
        form['question'] = "Wazzup"
        form['pub_date'] = '2014-04-09 10:48:17'
        response = response.form.submit('save_close')
        assert response.status_int == 302
        response = response.follow()
        assert "Poll added!" in response

        # Make sure the item was actually added
        table = response.html.find("table")
        rows = table.find("tbody").find_all("tr")
        assert len(rows) == 1
        _, question, pub_date, published = rows[0].find_all("td")
        assert question.find("a").string.strip() == "Wazzup"
        href = question.find("a").attrs["href"]
        assert href == "http://localhost/polls/1/edit"
        assert pub_date.string.strip() == '2014-04-09 10:48:17'
        assert published.string.strip() == 'No'

        # Visit the existing item to edit it and add a choice
        response = response.click(href=href)
        response = response.form.submit('add_choice')
        form = response.form
        form['choice_0_choice_text'] = 'Choice1'
        form['choice_0_votes'] = '5'
        response = response.form.submit('add_choice')
        form = response.form
        form['choice_1_choice_text'] = 'Choice2'
        form['choice_1_votes'] = '6'
        response = form.submit('save')
        assert response.status_int == 302
        response = response.follow()
        assert "Poll edited!" in response

        # Now delete that saved choice again and make sure it is persisted
        form = response.form
        assert form['choice_0_id'].value == '1'
        assert form['choice_0_choice_text'].value == 'Choice1'
        assert form['choice_1_id'].value == '2'
        assert form['choice_1_choice_text'].value == 'Choice2'
        assert 'choice_2_id' not in form.fields
        assert 'choice_2_choice_text' not in form.fields
        response = form.submit('delete_choice_0')
        assert response.status_int == 200
        form = response.form
        assert "delete_choice_1" not in form.fields
        response = form.submit('delete_choice_0')
        assert response.status_int == 200

        # Make sure it is gone
        form = response.form
        assert 'choice_0_id' not in form.fields
        assert 'choice_0_choice_text' not in form.fields
        assert 'choice_1_choice_text' not in form.fields
        response = form.submit('save_close')
        assert response.status_int == 302
        response = response.follow()
        assert "Poll edited!" in response

        # Create a second poll
        response = response.click(href="http://localhost/polls/new")
        response = response.form.submit('delete_choice_0')
        response = response.form.submit('delete_choice_0')
        form = response.form
        form['question'] = "Wazzup"
        form['pub_date'] = '2014-04-09 10:48:17'
        response = response.form.submit('save_close')
        response = response.follow()
        assert "Poll added!" in response

        # Delete the Poll
        form = response.form
        form['action'] = 'delete'
        form['items'] = ['1']
        response = form.submit('submit')
        assert response.status_int == 200

        # Press Cancel
        response = response.click(href="http://localhost/polls")
        assert response.status_int == 200

        # Delete (for real)
        form = response.form
        form['action'] = 'delete'
        form['items'] = ['1']
        response = form.submit('submit')
        assert response.status_int == 200

        # Confirm deletion
        response = response.form.submit('confirm_delete')
        assert response.status_int == 302
        response = response.follow()
        assert "1 Poll deleted!" in response
