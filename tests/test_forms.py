from pyramid_crud import forms
from webob.multidict import MultiDict
from wtforms.fields import StringField
import pytest


@pytest.fixture
def formdata():
    return MultiDict()


@pytest.fixture
def form():
    return forms.BaseModelForm


@pytest.fixture
def subform():

    class SubForm(forms.BaseModelForm):
        test = StringField()

    return SubForm


@pytest.fixture
def form_Model_one_pk(Model_one_pk):
    class Form_one_pk(forms.BaseModelForm):
        class Meta:
            model = Model_one_pk

    return Form_one_pk


class Test_BaseModelForm(object):

    def test_init_attrs(self, formdata):
        obj = object()
        f = forms.BaseModelForm(formdata, obj)
        assert f.formdata is formdata
        assert f.obj is obj

    def test_fieldsets_default(self, form):
        assert form().fieldsets == [(None, {'fields': []})]

    def test_fieldsets_default_with_fields(self, subform):
        assert subform().fieldsets == [(None, {'fields': ['test']})]

    def test_fieldsets_override(self, subform):

        class SubForm(subform):
            fieldsets = [('Title', {'fields': ['test']})]

        assert SubForm().fieldsets == [('Title', {'fields': ['test']})]

    def test__relationship_key(self, form_Model_one_pk, Model2_many_to_one):
        form = form_Model_one_pk

        class OtherForm(forms.BaseInLine):
            class Meta:
                model = Model2_many_to_one

        assert form()._relationship_key(OtherForm) == 'models'

    def test__relationship_key_ambigous(self, form_Model_one_pk,
                                        Model2_many_to_one_multiple):
        form = form_Model_one_pk

        class OtherForm(forms.BaseInLine):
            class Meta:
                model = Model2_many_to_one_multiple

        with pytest.raises(ValueError):
            form()._relationship_key(OtherForm)

    def test__relationship_key_none(self, form_Model_one_pk, Model2_basic):
        form = form_Model_one_pk

        class OtherForm(forms.BaseInLine):
            class Meta:
                model = Model2_basic

        with pytest.raises(ValueError):
            form()._relationship_key(OtherForm)

    def test__relationship_key_explicity(self, form_Model_one_pk,
                                         Model2_basic):
        form = form_Model_one_pk

        class OtherForm(forms.BaseInLine):
            class Meta:
                model = Model2_basic
            relationship_name = 'some_name'

        assert form()._relationship_key(OtherForm) == 'some_name'
