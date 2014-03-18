from pyramid_crud import forms
from webob.multidict import MultiDict
from wtforms.fields import StringField, IntegerField
from sqlalchemy import Column, String, Integer
from mock import MagicMock
import pytest


@pytest.fixture
def formdata():
    return MultiDict()


@pytest.fixture
def form():
    return forms.ModelForm


@pytest.fixture
def subform():

    class SubForm(forms.ModelForm):
        test = StringField()

    return SubForm


@pytest.fixture
def generic_obj(Base):

    class GenericModel(Base):
        id = Column(Integer, primary_key=True)
        test_text = Column(String)
        test_int = Column(Integer)
    return GenericModel


# tests for all forms that inherit from the ModelForm
class TestNormalModelForm(object):

    @pytest.fixture(autouse=True)
    def _prepare(self, normal_form, inline_form):
        self.base_form = normal_form
        self.inline_form = inline_form

    def test_init_attrs(self, formdata):
        obj = object()
        f = forms.ModelForm(formdata, obj)
        assert f.formdata is formdata
        assert f.obj is obj

    def test__relationship_key(self, Model2_many_to_one, Model_one_pk,
                               form_factory):
        form = form_factory(base=self.base_form, model=Model_one_pk)
        OtherForm = form_factory(base=self.inline_form,
                                 model=Model2_many_to_one)
        assert form()._relationship_key(OtherForm) == 'models'

    def test__relationship_key_ambigous(self, Model_one_pk,
                                        Model2_many_to_one_multiple,
                                        form_factory):
        form = form_factory(base=self.base_form, model=Model_one_pk)
        OtherForm = form_factory(base=self.inline_form,
                                 model=Model2_many_to_one_multiple)
        with pytest.raises(ValueError):
            form()._relationship_key(OtherForm)

    def test__relationship_key_none(self, Model_one_pk, Model2_basic,
                                    form_factory):
        form = form_factory(base=self.base_form, model=Model_one_pk)
        OtherForm = form_factory(base=self.inline_form, model=Model2_basic)

        with pytest.raises(ValueError):
            form()._relationship_key(OtherForm)

    def test__relationship_key_explicitly(self, Model_one_pk,
                                          Model2_basic, form_factory):

        form = form_factory(base=self.base_form, model=Model_one_pk)
        other_form_fields = {'relationship_name': 'some_name'}
        OtherForm = form_factory(base=self.inline_form, model=Model2_basic,
                                 fields=other_form_fields)
        assert form()._relationship_key(OtherForm) == 'some_name'

    def test_process(self, formdata, generic_obj):
        # TODO: Test that parent "process" is called, too.
        form = self.base_form()
        form.process_inline = MagicMock()
        form.process(formdata, generic_obj, test='Test23')
        form.process_inline.assert_called_once_with(formdata, generic_obj,
                                                    test='Test23')
    # TODO: Test process_inline

    def test_populate_obj(self, generic_obj):
        form = self.base_form()
        form.populate_obj_inline = MagicMock()
        form.populate_obj(generic_obj)
        form.populate_obj_inline.assert_called_once_with(generic_obj)

    # TODO: Test populate_obj_inline


# tests for all forms that inherit from _CoreModelForm (thus any form)
class TestAnyModelForm(object):

    @pytest.fixture(autouse=True)
    def _prepare(self, any_form, form_factory, model_factory):
        fields = {
            'test_text': StringField(),
            'test_int': IntegerField(),
        }
        self.form = form_factory(fields=fields, base=any_form)
        self.formdata = MultiDict(test_text='Test123', test_int=17)
        cols = [
            Column('id', Integer, primary_key=True),
            Column('test_text', String),
            Column('test_int', Integer),
        ]
        self.obj = model_factory(cols, name='GenericModel')

    def test_init(self):
        form = self.form(self.formdata)
        for key, value in self.formdata.items():
            assert getattr(form, key).data == value

    def test_init_obj_only(self):
        obj = self.obj(**self.formdata)
        form = self.form(obj=obj)
        for key, value in self.formdata.items():
            assert getattr(form, key).data == getattr(obj, key)

    def test_init_form_obj(self):
        obj = self.obj(test_text='ABC', test_int=3)
        form = self.form(self.formdata, obj)
        for key, value in self.formdata.items():
            assert getattr(form, key).data == value

    def test_init_form_one_val(self):
        obj = self.obj(**self.formdata)
        form = self.form(MultiDict(test_text='ABC'), obj)
        assert form.test_text.data == 'ABC'
        del self.formdata['test_text']
        for key, value in self.formdata.items():
            assert getattr(form, key).data == getattr(obj, key)

    def test_init_none(self):
        form = self.form()
        for key in self.formdata:
            assert getattr(form, key).data is None

    def test_title(self, form_factory, Model_one_pk, any_form):
        Form = form_factory(base=any_form, model=Model_one_pk)
        assert Form.title == 'Model'

    def test_title_plural(self, form_factory, Model_one_pk, any_form):
        Form = form_factory(base=any_form, model=Model_one_pk)
        assert Form.title_plural == 'Models'

    def test_name(self, form_factory, Model_one_pk, any_form):
        Form = form_factory(base=any_form, model=Model_one_pk)
        assert Form.name == 'model'

    def test_field_names(self, model_factory, form_factory, any_form):
        Model = model_factory([Column('val', Integer)])
        Form = form_factory(base=any_form, model=Model)
        field_names = ['val']
        assert Form.field_names == field_names

    def test_fieldsets(self, model_factory, form_factory, any_form):
        Model = model_factory([Column('val', Integer)])
        Form = form_factory(base=any_form, model=Model)
        fieldsets = [(None, {'fields': ['val']})]
        assert Form.fieldsets == fieldsets

    def test_fieldsets_empty(self, model_factory, form_factory, any_form):
        Model = model_factory()
        Form = form_factory(base=any_form, model=Model)
        fieldsets = [(None, {'fields': []})]
        assert Form.fieldsets == fieldsets

    def test_fieldsets_override(self, model_factory, form_factory, any_form):
        fieldsets = [('Test', {'fields': ['test', 'foo']})]
        Model = model_factory()
        Form = form_factory(base=any_form, model=Model,
                            fields={'fieldsets': fieldsets})
        assert Form.fieldsets == fieldsets

    def test_primary_keys(self, model_factory, form_factory, any_form,
                          DBSession):
        Model = model_factory()
        Form = form_factory(base=any_form, model=Model)
        obj = Model()
        DBSession.add(obj)
        DBSession.flush()
        assert Form(obj=obj).primary_keys == [('id', 1)]

    def test_primary_keys_multiple(self, model_factory, form_factory, any_form,
                                   DBSession):
        Model = model_factory([Column('id2', Integer, primary_key=True)])
        Form = form_factory(base=any_form, model=Model)
        obj = Model(id=1, id2=1)
        DBSession.add(obj)
        DBSession.flush()
        form_pks = sorted(Form(obj=obj).primary_keys, key=lambda t: t[0])
        assert form_pks == [('id', 1), ('id2', 1)]

    def test_primary_keys_no_obj(self, model_factory, form_factory, any_form):
        Model = model_factory()
        Form = form_factory(base=any_form, model=Model)
        with pytest.raises(AttributeError):
            Form().primary_keys

    def test_primary_keys_no_val(self, model_factory, form_factory, any_form):
        Model = model_factory()
        Form = form_factory(base=any_form, model=Model)
        assert Form(obj=Model()).primary_keys == [('id', None)]


# Tests for all forms that inherit from BaseInLine
class TestInlineModelForm(object):
    # TODO: test pks_from_formdata
    # TODO: test extra
    # TODO: test relationship_name
    pass
