from pyramid_crud import util


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
        assert util.get_pks(Model_one_pk) == ['id']

    def test_multiple_pks(self, Model_two_pk):
        assert util.get_pks(Model_two_pk) == ['id', 'id2']

    def test_different_colname(self, Model_diff_colname):
        assert util.get_pks(Model_diff_colname) == ['id']
