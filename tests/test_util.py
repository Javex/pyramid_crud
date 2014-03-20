from pyramid_crud import util
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
import six


def test_classproperty():

    class Test(object):
        val = 0

        @util.classproperty
        def test(self):
            return self.val

    assert Test.val == 0
    assert Test.test == 0
    Test.val = 7
    assert Test.val == 7
    assert Test.test == 7


class Test_get_pks(object):

    def test_single_pk(self, Model_one_pk):
        assert sorted(util.get_pks(Model_one_pk)) == ['id']

    def test_multiple_pks(self, Model_two_pk):
        assert sorted(util.get_pks(Model_two_pk)) == ['id', 'id2']

    def test_different_colname(self, Model_diff_colname):
        assert sorted(util.get_pks(Model_diff_colname)) == ['id']

    def test_with_relationship(self, model_factory):
        Parent = model_factory(name='Parent')
        child_cols = [
            Column('parent_id', ForeignKey('parent.id')),
        ]
        child_rels = {'parent': relationship(Parent, backref='children')}
        Child = model_factory(child_cols, 'Child', relationships=child_rels)
        assert sorted(util.get_pks(Child)) == ['id']


def test_meta_property():
    class Meta(type):
        @util.meta_property
        def test(self):
            return "Meta"

    class Test(six.with_metaclass(Meta, object)):
        pass

    class TestSub(Test):
        test = "TestSub"

    class TestSubSub(TestSub):
        test = "TestSubSub"

    class TestSubWithout(Test):
        pass

    class TestSubSubWithout(TestSubWithout):
        pass

    class TestSubSubInherit(TestSubSub):
        pass

    assert Test.test == "Meta"
    assert TestSub.test == "TestSub"
    assert TestSubSub.test == "TestSubSub"
    assert TestSubWithout.test == "Meta"
    assert TestSubSubWithout.test == "Meta"
    assert TestSubSubInherit.test == "TestSubSub"


def test_meta_property_new_meta():
    class Meta(type):
        @util.meta_property
        def test(self):
            return "Meta"

    class Test(object):
        test = "Test"

    class TestWithMeta(six.with_metaclass(Meta, Test)):
        pass

    assert Test.test == "Test"
    assert TestWithMeta.test == "Test"
