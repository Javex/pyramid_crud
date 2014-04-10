from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty


def get_pks(model):
    """
    Get a list of primary key attribute names, i.e. those attributes that
    represent a primary key.

    :param model: A model for which to search the keys.
    """
    pk_cols = set(pk.name for pk in inspect(model).primary_key)
    pk_attributes = []
    for prop in inspect(model).iterate_properties:
        if not isinstance(prop, ColumnProperty):
            continue
        if len(prop.columns) != 1:
            raise ValueError("Unexpected number of columns. Please report "
                             "this as a bug.")  # pragma: no cover
        if prop.columns[0].name in pk_cols:
            pk_attributes.append(prop.key)
    return pk_attributes


class meta_property(object):
    """
    A non-data-descriptor, that behaves like :class:`property` except that it
    only provides the getter part.

    This is to be used on a metaclass instead of :class:`property`. This will
    turn the method into a class property but additionally allows inheritance
    of property as an attribute on subclasses. Inherited attributes will always
    take precedence over the metaclass, no matter where it is defined.

    An example clarifies this:

    .. code-block:: python


        class Meta(type):
            @meta_property
            def test(self):
                return "Meta"


        class Test(six.with_metaclass(Meta, object)):
            pass


        class TestSub(Test):
            test = "TestSub"


        class TestSubWithout(Test):
            pass

        print(TestSub.test, TestSubWithout.test)

    This will print ``('TestSub', 'Meta')`` instead of ``('Meta', 'Meta')`` as
    it would happen when using the usual :class:`property`.
    """
    def __init__(self, fget):
        self.fget = fget
        if hasattr(fget, '__doc__') and fget.__doc__:
            self.__doc__ = fget.__doc__

    def __get__(self, obj, type_):
        if obj:
            return self.fget(obj)
        else:
            return self  # pragma: no cover
