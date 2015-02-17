from pyramid_crud import forms, fields
from webob.multidict import MultiDict
from wtforms.fields import StringField, IntegerField
import wtforms
from sqlalchemy import Column, String, Integer, ForeignKey, inspect
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.interfaces import MANYTOONE
try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch
from itertools import product
from wtforms.ext.sqlalchemy.fields import QuerySelectField
import pytest
import six


@pytest.fixture
def formdata():
    return MultiDict()


@pytest.fixture
def form():
    return forms.ModelForm


@pytest.fixture
def generic_obj(Base):

    class GenericModel(Base):
        id = Column(Integer, primary_key=True)
        test_text = Column(String)
        test_int = Column(Integer)
    return GenericModel


def get_obj_test_matrix():
    "Create a matrix to test different types of objects."
    test_matrix = []
    for type_ in ['No values', 'Parent only', 'Children only']:
        for children_no in range(2):
            for values_on_children_no in range(children_no + 1):
                test_matrix.append((type_, children_no,
                                    values_on_children_no))
    return test_matrix


def test_doc_copy():
    # Test regular behavior
    class A(object):
        "Test Parent"
        @classmethod
        def _add_relationship_fields(cls):
            pass

    @six.add_metaclass(forms._CoreModelMeta)
    class B(A):
        pass

    assert B.__doc__ == "Test Parent"


def test_doc_copy_no_override():
    # Test what happens if the child already has a docstring
    class A(object):
        "Test Parent"
        @classmethod
        def _add_relationship_fields(cls):
            pass

    @six.add_metaclass(forms._CoreModelMeta)
    class B(A):
        "Test Child"

    assert B.__doc__ == "Test Child"


def test_doc_copy_none():
    # Test what happens if noone has a docstring
    class A(object):
        @classmethod
        def _add_relationship_fields(cls):
            pass

    @six.add_metaclass(forms._CoreModelMeta)
    class B(A):
        pass

    assert not B.__doc__


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
        assert f._obj is obj

    def test_inline_id_change(self, form_factory, Model_one_pk):
        Form1 = form_factory(base=self.base_form, model=Model_one_pk)
        Form2 = form_factory(base=self.base_form, model=Model_one_pk)
        assert Form1.inlines is not Form2.inlines

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
        with pytest.raises(TypeError):
            form()._relationship_key(OtherForm)

    def test__relationship_key_none(self, Model_one_pk, Model2_basic,
                                    form_factory):
        form = form_factory(base=self.base_form, model=Model_one_pk)
        OtherForm = form_factory(base=self.inline_form, model=Model2_basic)

        with pytest.raises(TypeError):
            form()._relationship_key(OtherForm)

    def test__relationship_key_explicitly(self, Model_one_pk,
                                          Model2_basic, form_factory):

        form = form_factory(base=self.base_form, model=Model_one_pk)
        other_form_fields = {'relationship_name': 'some_name'}
        OtherForm = form_factory(base=self.inline_form, model=Model2_basic,
                                 fields=other_form_fields)
        assert form()._relationship_key(OtherForm) == 'some_name'

    def test_process(self, formdata, generic_obj):
        form = self.base_form()
        with patch.object(self.base_form.__bases__[0], 'process') as mocked:
            form.process_inline = MagicMock()
            form.process(formdata, generic_obj, test='Test23')
            form.process_inline.assert_called_once_with(formdata, generic_obj,
                                                        test='Test23')
            mocked.assert_called_once_with(formdata, generic_obj,
                                           test='Test23')

    def test_populate_obj(self, generic_obj):
        form = self.base_form()
        base = self.base_form.__bases__[0]
        with patch.object(base, 'populate_obj') as mocked:
            form.populate_obj_inline = MagicMock()
            form.populate_obj(generic_obj)
            form.populate_obj_inline.assert_called_once_with(generic_obj)
            mocked.assert_called_one_with(generic_obj)

    def test_validate(self, formdata, generic_obj):
        form = self.base_form(formdata, generic_obj)
        base = self.base_form.__bases__[0]
        with patch.object(base, 'validate') as mocked:
            form.validate_inline = MagicMock()
            assert form.validate()
            form.validate_inline.assert_called_once_with()
            mocked.assert_called_once_with()

    def test_validate_with_error(self, formdata, generic_obj):
        form = self.base_form(formdata, generic_obj)
        base = self.base_form.__bases__[0]
        with patch.object(base, 'validate') as mocked:
            mocked.return_value = False
            form.validate_inline = MagicMock()
            assert not form.validate()
            form.validate_inline.assert_called_once_with()
            mocked.assert_called_once_with()

    def test_validate_with_inline_error(self, formdata, generic_obj):
        form = self.base_form(formdata, generic_obj)
        base = self.base_form.__bases__[0]
        with patch.object(base, 'validate') as mocked:
            form.validate_inline = MagicMock()
            form.validate_inline.return_value = False
            assert not form.validate()
            form.validate_inline.assert_called_once_with()
            mocked.assert_called_once_with()

    def test_validate_with_both_error(self, formdata, generic_obj):
        form = self.base_form(formdata, generic_obj)
        base = self.base_form.__bases__[0]
        with patch.object(base, 'validate') as mocked:
            mocked.return_value = False
            form.validate_inline = MagicMock()
            form.validate_inline.return_value = False
            assert not form.validate()
            form.validate_inline.assert_called_once_with()
            mocked.assert_called_once_with()


class TestManyToOneAndOneToOne(object):

    @pytest.fixture(params=[lambda x: x, backref])
    def _backref(self, request):
        return request.param

    @pytest.fixture(params=[True, False])
    def one_to_one(self, request):
        return request.param

    def test_base(self, form_factory, model_factory, normal_form, one_to_one):
        ParentModel = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
            Column('test_text', String),
        ]
        if one_to_one:
            bref = backref('child', uselist=False)
        else:
            bref = 'children'
        child_rels = {'parent': relationship(ParentModel, backref=bref)}
        ChildModel = model_factory(child_cols, 'Child',
                                   relationships=child_rels)
        ChildForm = form_factory(model=ChildModel, base=normal_form)

        form = ChildForm()
        assert hasattr(form, 'parent')
        assert list(form.parent.iter_choices()) == []

    def test_base_with_choices(
            self, form_factory, model_factory, normal_form, DBSession,
            one_to_one):
        ParentModel = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
        ]
        if one_to_one:
            bref = backref('child', uselist=False)
        else:
            bref = 'children'
        child_rels = {'parent': relationship(ParentModel, backref=bref)}
        ChildModel = model_factory(child_cols, 'Child',
                                   relationships=child_rels)
        ChildForm = form_factory(model=ChildModel, base=normal_form)

        objs = [ParentModel(), ParentModel()]
        DBSession.add_all(objs)

        form = ChildForm()
        assert hasattr(form, 'parent')
        field_items = list(form.parent._get_object_list())
        field_items = [i[1] for i in field_items]
        assert field_items == objs

    def test_one_to_many_with_many_to_one(
            self, form_factory, model_factory, normal_form, DBSession,
            inline_form, _backref):
        ParentModel = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
        ]
        child_rels = {
            'parent': relationship(ParentModel, backref=_backref('children'))
        }
        ChildModel = model_factory(child_cols, 'Child',
                                   relationships=child_rels)
        ChildForm = form_factory(model=ChildModel, base=inline_form)
        ParentForm = form_factory({'inlines': [ChildForm]}, model=ParentModel,
                                  base=normal_form)
        parent = ParentModel()
        parent.children.append(ChildModel())

        form = ParentForm(obj=parent)
        assert len(form.inline_fieldsets) == 1
        for child_form in form.inline_fieldsets['child'][1]:
            assert not hasattr(child_form, 'parent')

    def test__add_relationship_fields(self, form_factory, model_factory,
                                     any_form, DBSession):
        ParentModel = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
        ]
        child_rels = {'parent': relationship(ParentModel, backref='children')}
        ChildModel = model_factory(child_cols, 'Child',
                                   relationships=child_rels)

        attrs = {
            '_find_relationships_for_query': MagicMock(
                return_value=[ChildModel.parent.property])
        }

        ChildForm = form_factory(attrs, base=any_form, model=ChildModel)
        assert ChildForm.parent.field_class == QuerySelectField
        form = ChildForm()
        assert form.parent.data is None

    def test__add_relationship_fields_obj(self, form_factory, model_factory,
                                          any_form, DBSession):
        ParentModel = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
        ]
        child_rels = {'parent': relationship(ParentModel, backref='children')}
        ChildModel = model_factory(child_cols, 'Child',
                                   relationships=child_rels)

        attrs = {
            '_find_relationships_for_query': MagicMock(
                return_value=[ChildModel.parent.property])
        }

        ChildForm = form_factory(attrs, base=any_form, model=ChildModel)
        assert ChildForm.parent.field_class == QuerySelectField

        obj = ChildModel()
        form = ChildForm(obj=obj)
        assert form.parent.data is None

        obj.parent = ParentModel()
        form = ChildForm(obj=obj)
        assert form.parent.data == obj.parent
        assert form.parent().startswith('<select')

    def test__add_relationship_fields_missing_session(
            self, form_factory, model_factory, any_form, DBSession):
        ParentModel = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
        ]
        child_rels = {'parent': relationship(ParentModel, backref='children')}
        ChildModel = model_factory(child_cols, 'Child',
                                   relationships=child_rels)

        with pytest.raises(ValueError):
            class ChildForm(any_form):

                class Meta:
                    model = ChildModel

                @classmethod
                def _find_relationships_for_query(cls):
                    return [ChildModel.parent.property]

    def test__add_relationship_fields_exclude_one_to_may(
            self, form_factory, model_factory, any_form, DBSession):
        parent_rels = {
            'children': relationship(lambda: ChildModel, backref='parent')
        }
        ParentModel = model_factory(name='Parent', relationships=parent_rels)
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
        ]
        ChildModel = model_factory(child_cols, 'Child')

        attrs = {
            '_find_relationships_for_query': MagicMock(
                return_value=[inspect(ParentModel.children).property])
        }
        ParentForm = form_factory(attrs, base=any_form, model=ParentModel)
        assert not hasattr(ParentForm, 'children')

    def test__find_relationships_for_query_normal(
            self, form_factory, model_factory, normal_form):
        ParentModel = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
        ]
        child_rels = {'parent': relationship(ParentModel, backref='children')}
        ChildModel = model_factory(child_cols, 'Child',
                                   relationships=child_rels)

        ChildForm = form_factory(base=normal_form, model=ChildModel)
        rels = ChildForm._find_relationships_for_query()
        assert rels == [ChildModel.parent.property]

    def test__find_relationships_for_query_inline(
            self, form_factory, model_factory, normal_form, inline_form):
        ParentModel = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
        ]
        child_rels = {'parent': relationship(ParentModel, backref='children')}
        ChildModel = model_factory(child_cols, 'Child',
                                   relationships=child_rels)

        ChildForm = form_factory(base=inline_form, model=ChildModel)
        rels = ChildForm._find_relationships_for_query()
        assert rels == []


@pytest.fixture(params=[0, 1, 2])
def form_with_inlines(request, form_factory, model_factory,
                      normal_form):
    inline_form = forms.BaseInLine
    "Prepare a form with inlines"
    # request.param denotes number of different inline forms
    def get_default_cols():
        cols = [
            Column('test_text', String),
            Column('test_int', Integer),
        ]
        return cols
    ParentModel = model_factory(get_default_cols(), 'Parent')
    child1_cols = get_default_cols() + \
        [Column('parent_id', ForeignKey('parent.id'))]
    child1_rel = relationship(ParentModel, backref='child1')
    ChildModel1 = model_factory(child1_cols, 'Child1',
                                relationships={'parent': child1_rel})
    child2_cols = get_default_cols() + \
        [Column('parent_id', ForeignKey('parent.id'))]
    child2_rel = relationship(ParentModel, backref='child2')
    ChildModel2 = model_factory(child2_cols, 'Child2',
                                relationships={'parent': child2_rel})
    ChildModel1Form = form_factory(base=inline_form,
                                   name='ChildModel1Form',
                                   model=ChildModel1)
    ChildModel2Form = form_factory(base=inline_form,
                                   name='ChildModel2Form',
                                   model=ChildModel2)
    if request.param == 0:
        inlines = []
    elif request.param == 1:
        inlines = [ChildModel1Form]
    elif request.param == 2:
        inlines = [ChildModel1Form, ChildModel2Form]
    else:
        raise ValueError("Testing count %d not implemented"
                         % request.param)
    ParentModelForm = form_factory(fields={'inlines': inlines},
                                   base=normal_form,
                                   name='ParentModelForm',
                                   model=ParentModel)
    return ParentModelForm


@pytest.fixture(params=[0, 1])
def formdata_with_inlines(request, form_with_inlines):
    Form = form_with_inlines
    "Prepare formdata to be processed"
    # request.param denotes number of inline forms with data
    formdata = MultiDict(test_int='1', test_text='parent')
    form_count = str(request.param)
    for inline_index in range(1, len(Form.inlines) + 1):
        formdata['child%d_count' % inline_index] = form_count
        for item_index in range(request.param):
            int_key = 'child%d_%d_test_int' % (inline_index, item_index)
            text_key = 'child%d_%d_test_text' % (inline_index, item_index)
            int_val = '%d%d' % (inline_index, item_index)
            text_val = 'text_child%d_%d' % (inline_index, item_index)
            formdata[int_key] = int_val
            formdata[text_key] = text_val
    return formdata, form_count


@pytest.fixture(params=get_obj_test_matrix())
def obj_with_inlines(request, form_with_inlines):
    # type_: How to initialize values, e.g. no values or only put values on
    # the parent.
    #
    # children_no: How many children the parent should have.
    #
    # values_on_children_no: How many children should get values if type_
    # determines there should be any
    type_, children_no, values_on_children_no = request.param

    Form = form_with_inlines
    inline_count = len(Form.inlines)

    # create parent
    obj = Form.Meta.model()

    # create desired number of children on each inline form
    for child_no, (index, inline) in \
            product(range(children_no), enumerate(Form.inlines, 1)):
        inline_model = inline.Meta.model
        child_obj = inline_model()
        assert inspect(inline_model).mapped_table.name == 'child%d' % index
        getattr(obj, 'child%d' % index).append(child_obj)

    # pass in values depending on type_
    if type_ == 'Parent only':
        obj.test_text = 'ParentModel'
        obj.test_int = 2
    if type_ == 'Children only':
        for inline_index in range(1, inline_count + 1):
            children = getattr(obj, 'child%d' % inline_index)
            for index, child in enumerate(children[:values_on_children_no]):
                text_val = 'text_child%d_model_%d' % (inline_index, index)
                int_val = int('1%d%d' % (inline_index, index))
                child.test_text = text_val
                child.test_int = int_val
    return (type_, children_no, values_on_children_no), obj


class TestNormalModelFormWithInline(object):

    @pytest.fixture
    def _basic_form_with_inline(self, model_factory, form_factory, inline_form,
                                normal_form):
        ParentModel = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
            Column('test_text', String),
        ]
        child_rels = {'parent': relationship(ParentModel, backref='children')}
        ChildModel = model_factory(child_cols, 'Child',
                                   relationships=child_rels)
        ChildForm = form_factory(model=ChildModel, base=inline_form)
        ParentForm = form_factory({'inlines': [ChildForm]}, model=ParentModel,
                                  base=normal_form)
        return ParentForm, ChildForm

    @pytest.fixture(params=[0, 1, 2])
    def extra(self, request):
        return request.param

    def _parse_fixtures(self, form_with_inlines=None,
                        formdata_with_inlines=None,
                        obj_with_inlines=None):
        if form_with_inlines:
            self.Form = form_with_inlines
            self.inline_count = len(self.Form.inlines)
            self.ParentModel = self.Form.Meta.model

        if formdata_with_inlines:
            self.formdata, self.form_count = formdata_with_inlines

        if obj_with_inlines:
            obj_cfg, obj = obj_with_inlines
            self.value_type = obj_cfg[0]
            self.children_no = obj_cfg[1]
            self.values_on_children_no = obj_cfg[2]
            self.obj = obj

    def test_process_inline(self, form_with_inlines, formdata_with_inlines):
        self._parse_fixtures(form_with_inlines, formdata_with_inlines)
        form = self.Form(self.formdata)
        assert len(form.inlines) == self.inline_count
        for inline_index, inline in enumerate(form.inlines):
            inline_ref, forms = form.inline_fieldsets[inline.name]
            assert inline_ref is inline
            assert len(forms) == int(self.form_count)
            for form_index, inline_form in enumerate(forms):
                assert inline_form.is_extra is True
                for field in inline_form:
                    assert str(field.data) == self.formdata[field.name]

    def test_process_inline_none(self, form_with_inlines):
        self._parse_fixtures(form_with_inlines)
        form = self.Form()
        form.process_inline()
        assert len(form.inlines) == int(self.inline_count)
        for inline_index, inline in enumerate(form.inlines):
            inline_ref, forms = form.inline_fieldsets[inline.name]
            assert inline_ref is inline
            assert len(forms) == 0

    def test_process_inline_with_obj(self, form_with_inlines,
                                     obj_with_inlines):
        self._parse_fixtures(form_with_inlines, None, obj_with_inlines)
        form = self.Form(obj=self.obj)
        if self.value_type == 'Parent only':
            assert form.test_text.data == 'ParentModel'
            assert form.test_int.data == 2
        else:
            assert form.test_text.data is None
            assert form.test_int.data is None
        for inline_index, inline in enumerate(form.inlines, 1):
            inline_ref, forms = form.inline_fieldsets[inline.name]
            assert inline_ref is inline
            child_key = 'child%d' % inline_index
            children = getattr(form._obj, child_key)
            assert len(children) == len(forms) == self.children_no
            for child_index, (child, inline_form) in \
                    enumerate(zip(children, forms)):
                assert inline_form.is_extra is False
                if self.value_type == 'Children only':
                    text_key = ('child%d_%d_test_text'
                                % (inline_index, child_index))
                    int_key = ('child%d_%d_test_int'
                               % (inline_index, child_index))
                    assert inline_form.test_text.name == text_key
                    assert inline_form.test_int.name == int_key
                    if child_index <= self.values_on_children_no:
                        assert inline_form.test_text.data == child.test_text
                        assert inline_form.test_int.data == child.test_int
                else:
                    assert inline_form.test_text.data is None
                    assert inline_form.test_int.data is None

    def test_process_inline_obj_and_formdata(
            self, form_with_inlines, formdata_with_inlines, obj_with_inlines):
        self._parse_fixtures(form_with_inlines, formdata_with_inlines,
                             obj_with_inlines)
        form = self.Form(self.formdata, self.obj)
        assert form.test_text.data == 'parent'
        assert form.test_int.data == 1
        for inline_index, inline in enumerate(form.inlines, 1):
            inline_ref, forms = form.inline_fieldsets[inline.name]
            assert inline_ref is inline
            child_key = 'child%d' % inline_index
            children = getattr(form._obj, child_key)
            # either number of objs or items in formdata
            data_count = max(len(children), int(self.form_count))
            assert data_count == len(forms)
            for child_index, (child, inline_form) in \
                    enumerate(zip(children, forms)):
                if self.value_type == 'Children only':
                    text_key = ('child%d_%d_test_text'
                                % (inline_index, child_index))
                    int_key = ('child%d_%d_test_int'
                               % (inline_index, child_index))
                    assert inline_form.test_text.name == text_key
                    assert inline_form.test_int.name == int_key
                    if child_index < int(self.form_count):
                        if child_index <= self.values_on_children_no:
                            assert inline_form.is_extra is False
                        else:
                            assert inline_form.is_extra is True
                        assert str(inline_form.test_text.data) == \
                            self.formdata[text_key]
                        assert str(inline_form.test_int.data) == \
                            self.formdata[int_key]
                    elif child_index <= self.values_on_children_no:
                        assert inline_form.is_extra is False
                        assert inline_form.test_text.data == child.test_text
                        assert inline_form.test_int.data == child.test_int
                    else:
                        assert inline_form.is_extra is False
                        assert inline_form.test_text.data is None
                        assert inline_form.test_int.data is None

    def test_process_inline_add(self, _basic_form_with_inline):
        ParentForm, ChildForm = _basic_form_with_inline
        formdata = MultiDict(add_child='Add')
        form = ParentForm(formdata)
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert len(forms) == 1
        assert inline == ChildForm
        form = forms[0]
        assert form.is_extra is True
        assert form.test_text.data is None

    def test_process_inline_extra(self, extra, _basic_form_with_inline):
        ParentForm, ChildForm = _basic_form_with_inline
        ChildForm.extra = extra
        form = ParentForm()
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert inline is ChildForm
        assert inline.extra == extra
        assert len(forms) == extra
        for form in forms:
            assert form.is_extra is True
            assert form.test_text.data is None

    def test_process_inline_extra_obj(self, extra, _basic_form_with_inline):
        ParentForm, ChildForm = _basic_form_with_inline
        ChildForm.extra = extra
        parent = ParentForm.Meta.model()
        child = ChildForm.Meta.model()
        child.test_text = 'TestValue'
        child.parent = parent

        form = ParentForm(obj=parent)
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert inline is ChildForm
        assert inline.extra == extra
        assert len(forms) == 1
        for form in forms:
            assert form.is_extra is False
            assert form.test_text.data == 'TestValue'

    def test_process_inline_extra_formdata(self,
                                           _basic_form_with_inline):
        ParentForm, ChildForm = _basic_form_with_inline
        ChildForm.extra = 3
        formdata = MultiDict(child_count="5")
        form = ParentForm(formdata)
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert inline is ChildForm
        assert inline.extra == 3
        assert len(forms) == 5
        for form in forms:
            assert form.is_extra is True
            assert form.test_text.data is None

    def test_process_inline_extra_obj_formdata(
            self, _basic_form_with_inline):
        ParentForm, ChildForm = _basic_form_with_inline
        ChildForm.extra = 3
        parent = ParentForm.Meta.model()
        parent.children.append(ChildForm.Meta.model(test_text='TestValue'))
        formdata = MultiDict(child_count="5")

        form = ParentForm(formdata, parent)
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert inline is ChildForm
        assert inline.extra == 3
        assert len(forms) == 5
        for index, form in enumerate(forms):
            if index == 0:
                assert form.is_extra is False
                assert form.test_text.data == 'TestValue'
            else:
                assert form.is_extra is True
                assert form.test_text.data is None

    def test_process_inline_delete(
            self, _basic_form_with_inline, DBSession):
        ParentForm, ChildForm = _basic_form_with_inline
        parent = ParentForm.Meta.model()
        parent.children.append(ChildForm.Meta.model())
        parent.children.append(ChildForm.Meta.model())
        DBSession.add(parent)
        DBSession.flush()
        child0_id = parent.children[0].id
        child1_id = parent.children[1].id
        formdata = MultiDict(child_count="2",
                             delete_child_0=True, child_0_id=child0_id,
                             delete_child_1=True, child_1_id=child1_id)
        assert len(parent.children) == 2
        form = ParentForm(formdata, parent)
        assert len(parent.children) == 0
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert inline is ChildForm
        assert len(forms) == 0

    def test_process_inline_delete_extra_field(
            self, _basic_form_with_inline):
        ParentForm, ChildForm = _basic_form_with_inline
        formdata = MultiDict(child_count='1', delete_child_0='y')
        form = ParentForm(formdata)
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert inline is ChildForm
        assert len(forms) == 0

        formdata = MultiDict(child_count='1')
        form = ParentForm(formdata)
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert inline is ChildForm
        assert len(forms) == 1
        form = forms[0]
        assert form.is_extra is True
        assert form.test_text.data is None

    def test_process_inline_delete_nonlast(
            self, _basic_form_with_inline, DBSession):
        ParentForm, ChildForm = _basic_form_with_inline
        parent = ParentForm.Meta.model()
        parent.children.append(ChildForm.Meta.model())
        DBSession.add(parent)
        DBSession.flush()
        formdata = MultiDict(
            child_count='2', delete_child_0='y',
            child_0_id=parent.children[0].id,
            child_0_test_text='ABC')
        form = ParentForm(formdata, parent)
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert inline is ChildForm
        assert len(forms) == 1
        [form] = forms
        assert form.is_extra is True
        assert form.test_text.data is None

    def test_process_inline_no_relationship(
            self, model_factory, form_factory, inline_form, normal_form):
        Model2 = model_factory(name='Model2')
        Form2 = form_factory(model=Model2, base=inline_form)
        Model1 = model_factory(name='Model1')
        Form1 = form_factory({'inlines': [Form2]}, model=Model1,
                             base=normal_form)
        with pytest.raises(TypeError):
            Form1()

    def test_populate_obj_inline_edit(self, _basic_form_with_inline,
                                      DBSession):
        ParentForm, ChildForm = _basic_form_with_inline
        child = ChildForm.Meta.model(test_text='TestVal')
        parent = ParentForm.Meta.model()
        parent.children.append(child)
        DBSession.add(parent)
        DBSession.flush()
        assert parent.id is not None
        assert child.id is not None
        assert child.parent_id is not None
        formdata = MultiDict(child_count='1', child_0_test_text='EditVal',
                             child_0_id=str(child.id))
        form = ParentForm(formdata, parent)
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert inline is ChildForm
        assert len(forms) == 1
        inline_form = forms[0]
        assert inline_form.is_extra is False
        assert inline_form.test_text.data == 'EditVal'
        assert child.test_text == 'TestVal'
        assert len(parent.children) == 1
        form.populate_obj(parent)
        assert len(parent.children) == 1
        assert child.test_text == 'EditVal'
        assert inline_form.test_text.data == 'EditVal'

    def test_populate_obj_inline_new_obj(self, _basic_form_with_inline,
                                         DBSession):
        ParentForm, ChildForm = _basic_form_with_inline
        parent = ParentForm.Meta.model()
        DBSession.add(parent)
        DBSession.flush()
        assert parent.id is not None
        formdata = MultiDict(child_count='1', child_0_test_text='NewVal')
        form = ParentForm(formdata, parent)
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert inline is ChildForm
        assert len(forms) == 1
        inline_form = forms[0]
        assert inline_form.is_extra is True
        assert inline_form.test_text.data == 'NewVal'
        assert len(parent.children) == 0
        form.populate_obj(parent)
        assert inline_form.test_text.data == 'NewVal'
        assert len(parent.children) == 1
        child = parent.children[0]
        assert child.test_text == 'NewVal'

    def test_populate_obj_inline_missing_obj(self, _basic_form_with_inline,
                                             DBSession):
        ParentForm, ChildForm = _basic_form_with_inline
        child = ChildForm.Meta.model()
        parent = ParentForm.Meta.model()
        parent.children.append(child)
        DBSession.add(parent)
        DBSession.flush()
        assert parent.id is not None
        formdata = MultiDict(child_count='1', child_0_test_text='NewVal',
                             child_0_id=str(child.id))
        form = ParentForm(formdata, parent)
        assert len(form.inline_fieldsets) == 1
        inline, forms = form.inline_fieldsets['child']
        assert inline is ChildForm
        assert len(forms) == 1
        inline_form = forms[0]
        assert inline_form.is_extra is False
        assert inline_form.test_text.data == 'NewVal'
        assert len(parent.children) == 1

        DBSession.delete(child)
        DBSession.expire(parent)
        assert len(parent.children) == 0
        with pytest.raises(LookupError):
            form.populate_obj(parent)
        assert len(parent.children) == 0

    def test_validate_inline(self, form_with_inlines, formdata_with_inlines):
        self._parse_fixtures(form_with_inlines, formdata_with_inlines)
        form = self.Form(self.formdata)
        assert form.validate_inline()

    def test_validate_inline_nodata(self, model_factory, form_factory,
                                    inline_form, normal_form):
        ParentModel = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
            Column('test_text', String, nullable=False),
        ]
        child_rels = {'parent': relationship(ParentModel, backref='children')}
        ChildModel = model_factory(child_cols, 'Child',
                                   relationships=child_rels)
        ChildForm = form_factory(model=ChildModel, base=inline_form)
        ParentForm = form_factory({'inlines': [ChildForm]}, model=ParentModel,
                                  base=normal_form)

        form = ParentForm(MultiDict({'child_count': '1'}))
        assert not form.validate_inline()
        assert len(form.errors) == 1
        assert 'child_0_test_text' in form.errors
        inline_err = form.inline_fieldsets["child"][1][0].errors
        assert len(inline_err) == 1
        assert 'test_text' in inline_err

    def test_validate_inline_missing_data_on_persisted(
            self, model_factory, form_factory, inline_form, normal_form,
            DBSession):
        ParentModel = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
            Column('test_text', String, nullable=False),
        ]
        child_rels = {'parent': relationship(ParentModel, backref='children')}
        ChildModel = model_factory(child_cols, 'Child',
                                   relationships=child_rels)
        ChildForm = form_factory(model=ChildModel, base=inline_form)
        ParentForm = form_factory({'inlines': [ChildForm]}, model=ParentModel,
                                  base=normal_form)

        parent = ParentModel()
        child = ChildForm.Meta.model(test_text='foo')
        parent.children.append(child)
        DBSession.add(child)
        DBSession.flush()
        assert child.id is not None

        form = ParentForm(MultiDict({'child_count': '1',
                                     'child_0_test_text': '',
                                     'child_0_id': str(child.id)}),
                          obj=parent)
        assert not form.validate_inline()
        assert len(form.errors) == 1
        assert 'child_0_test_text' in form.errors
        inline_err = form.inline_fieldsets["child"][1][0].errors
        assert len(inline_err) == 1
        assert 'test_text' in inline_err

    def test_validate_inline_one_valid(self, _basic_form_with_inline):
        ParentForm, _ = _basic_form_with_inline
        parent = ParentForm()
        child = MagicMock()
        form1, form2 = MagicMock(), MagicMock()
        form1.validate.return_value = False
        form1.errors = {}
        parent.inlines = [child]
        parent.inline_fieldsets = {'child': (child, [form1, form2])}
        assert not parent.validate_inline()
        assert form1.validate.assert_called_once()
        assert form2.validate.assert_called_once()


# tests for all forms that inherit from _CoreModelForm (thus any form)
class TestAnyModelForm(object):

    @pytest.fixture(autouse=True)
    def _prepare(self, any_form, form_factory, model_factory):
        fields = {
            'test_text': StringField(),
            'test_int': IntegerField(),
        }
        self.form = form_factory(fields=fields, base=any_form)
        self.formdata = MultiDict(test_text='Test123', test_int='17')
        cols = [
            Column('id', Integer, primary_key=True),
            Column('test_text', String),
            Column('test_int', Integer),
        ]
        self.obj = model_factory(cols, name='GenericModel')

    def test_init(self):
        form = self.form(self.formdata)
        for key, value in self.formdata.items():
            assert str(getattr(form, key).data) == value

    def test_init_obj_only(self):
        obj = self.obj(**self.formdata)
        form = self.form(obj=obj)
        for key, value in self.formdata.items():
            assert getattr(form, key).data == getattr(obj, key)

    def test_init_form_obj(self):
        obj = self.obj(test_text='ABC', test_int=3)
        form = self.form(self.formdata, obj)
        for key, value in self.formdata.items():
            assert str(getattr(form, key).data) == value

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

    def test_get_fieldsets(self, model_factory, form_factory, any_form):
        Model = model_factory([Column('val', Integer)])
        Form = form_factory(base=any_form, model=Model)
        form = Form()
        fieldsets = [{'title': '', 'fields': [form.val],
                      'template': 'horizontal'}]
        assert form.get_fieldsets() == fieldsets

    def test_get_fieldsets_empty(self, model_factory, form_factory, any_form):
        Model = model_factory()
        Form = form_factory(base=any_form, model=Model)
        form = Form()
        fieldsets = [{'title': '', 'fields': [], 'template': 'horizontal'}]
        assert form.get_fieldsets() == fieldsets

    def test_get_fieldsets_override(self, model_factory, form_factory,
                                    any_form):
        fieldsets = [{'title': 'Test', 'fields': ['test_text'],
                      'template': 'horizontal'}]
        self.form.fieldsets = fieldsets
        form = self.form()
        expected = []
        for fieldset in fieldsets:
            copy = dict(fieldset)
            expected.append(copy)
        expected[0]['fields'] = [form.test_text]
        assert form.get_fieldsets() == expected

    def test_get_fieldsets_override_default_template(
            self, model_factory, form_factory, any_form):
        fieldsets = [{'title': 'Test', 'fields': ['test_text']}]
        self.form.fieldsets = fieldsets
        form = self.form()
        expected = []
        for fieldset in fieldsets:
            copy = dict(fieldset)
            expected.append(copy)
        expected[0]['template'] = 'horizontal'
        expected[0]['fields'] = [form.test_text]
        assert form.get_fieldsets() == expected

    def test_get_fieldsets_no_csrf_token(self, model_factory, form_factory,
                                         any_form):
        Model = model_factory([Column('csrf_token', Integer)])
        Form = form_factory(base=any_form, model=Model)
        form = Form()
        fieldsets = [{'title': '', 'fields': [], 'template': 'horizontal'}]
        assert form.get_fieldsets() == fieldsets

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


def test_get_session(model_factory, form_factory, any_form,
                     DBSession):
    cols = [
        Column('test_unique', String, unique=True)
    ]
    model = model_factory(cols)

    @classmethod
    def get_session(cls):
        return DBSession
    fields = {
        'get_session': get_session
    }
    form = form_factory(fields, base=any_form, model=model)
    assert form.get_session() == DBSession


# Tests for all forms that inherit from BaseInLine
class TestInlineModelForm(object):
    # TODO: test pks_from_formdata
    pass


class TestCSRFForm(object):

    @pytest.fixture(autouse=True)
    def _prepare(self, pyramid_request, csrf_token):
        self.request = pyramid_request
        self.token = csrf_token

        class CSRFSub(forms.CSRFForm):
            pass
        self.Form = CSRFSub
        self.form = self.Form(csrf_context=self.request)

    def test_generate_csrf_token(self):
        assert self.form.generate_csrf_token(self.request) == self.token

    def test_token_field(self):
        assert self.form.csrf_token._value() == self.token

    def test_validate(self):
        formdata = MultiDict()
        formdata['csrf_token'] = self.token
        form = self.Form(formdata, csrf_context=self.request)
        assert form.validate()

    def test_validate_fail(self):
        formdata = MultiDict()
        formdata['csrf_token'] = 'WRONG'
        self.request.client_addr = ''
        form = self.Form(formdata, csrf_context=self.request)
        with patch('pyramid_crud.forms.log') as mock:
            assert not form.validate()
            assert mock.warn.call_count == 1


class TestMultiField(object):

    @pytest.fixture(autouse=True, params=[fields.MultiCheckboxField,
                                          fields.MultiHiddenField])
    def _prepare(self, request):
        class Form(wtforms.Form):
            items = request.param(choices=[('1', '1'), ('2', '2')])
        self.Form = Form

    def test_one_value(self):
        formdata = MultiDict()
        formdata['items'] = '1'
        form = self.Form(formdata)
        assert form.items.data == ['1']
        assert form.validate()

    def test_multiple_values(self):
        formdata = MultiDict()
        formdata.add('items', '1')
        formdata.add('items', '2')
        form = self.Form(formdata)
        assert form.items.data == ['1', '2']
        assert form.validate()

    def test_no_value(self):
        formdata = MultiDict()
        form = self.Form(formdata)
        assert not form.items.data
        assert form.validate()

    def test_invalid_choice(self):
        formdata = MultiDict()
        formdata['items'] = '3'
        form = self.Form(formdata)
        assert not form.validate()
        [err_msg] = form.errors['items']
        assert 'items does not exist anymore' in err_msg


class TestMultiCheckboxField(object):

    @pytest.fixture(autouse=True)
    def _prepare(self):
        class Form(wtforms.Form):
            items = fields.MultiCheckboxField(choices=[('1', ''), ('2', '')])
        self.Form = Form

    def test_output(self):
        form = self.Form()
        for index, item in enumerate(form.items, 1):
            expected = ('<input id="items-%d" name="items" type="checkbox" '
                        'value="%d">' % (index-1, index))
            assert str(item) == expected


class TestMultiHiddenField(object):

    @pytest.fixture(autouse=True)
    def _prepare(self):
        class Form(wtforms.Form):
            items = fields.MultiHiddenField(choices=[('1', ''), ('2', '')])
        self.Form = Form

    def test_output(self):
        form = self.Form()
        for index, item in enumerate(form.items, 1):
            expected = ('<input id="items-%d" name="items" type="hidden" '
                        'value="%d">' % (index-1, index))
            assert str(item) == expected


def test_select_field():
    class Form(wtforms.Form):
        select = fields.SelectField(choices=[('', 'Empty'), ('1', 'Test')])
    formdata = MultiDict()
    formdata['select'] = '1'
    form = Form(formdata)
    assert form.validate()


def test_select_field_invalid_choice():
    class Form(wtforms.Form):
        select = fields.SelectField(choices=[('', 'Empty'), ('1', 'Test')])
    formdata = MultiDict()
    formdata['select'] = '2'
    form = Form()
    assert not form.validate()
    [err_msg] = form.errors['select']
    assert 'select an action' in err_msg


def test_select_field_empty_choice():
    class Form(wtforms.Form):
        select = fields.SelectField(choices=[('', 'Empty'), ('1', 'Test')])
    formdata = MultiDict()
    formdata['select'] = ''
    form = Form(formdata)
    assert not form.validate()
    [err_msg] = form.errors['select']
    assert 'select an action' in err_msg
