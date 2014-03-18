from sqlalchemy.inspection import inspect


def get_pks(model):
    """
    Get a list of primary key attribute names, i.e. those attributes that
    represent a primary key.

    :param model: A model for which to search the keys.
    """
    pk_cols = set(pk.name for pk in inspect(model).primary_key)
    pk_attributes = []
    for prop in inspect(model).iterate_properties:
        if len(prop.columns) != 1:
            raise ValueError("Unexpected number of columns. Please report "
                             "this as a bug.")
        if prop.columns[0].name in pk_cols:
            pk_attributes.append(prop.key)
    return pk_attributes


class classproperty(object):
    """
    A decorator to turn a method into a property on a class. Behaves the same
    as a :cls:`property` only for classes instead of instances. Only supports
    the get part.
    """

    def __init__(self, getter):
        self.getter = getter
        self.__doc__ = getter.__doc__

    def __get__(self, instance, owner):
        return self.getter(owner)


class meta_property(property):
    """
    A direct subclass of :class:`property` that uses an overriden value on
    a class in precedence of the value returned by the decorator.

    This is to be used on a metaclass instead of :class:`property`. This will
    turn the method into a class property but additionally allows inheritance
    of property as an attribute on subclasses.

    An example clarifies this:

    .. code-block:: python


        class Meta(type):
            @meta_property
            def test(self):
                return "Meta"


        class Test(object):
            __metaclass__ = Meta


        class TestSub(Test):
            test = "TestSub"


        class TestSubWithout(Test):
            pass

        print(TestSub.test, TestSubWithout.test)

    This will print ``('TestSub', 'Meta')`` instead of ``('Meta', 'Meta')`` as
    it would happen when using the usual :class:`property`.
    """
    def __init__(self, fget, fset=None, fdel=None, doc=None):
        self.key = fget.__name__
        super(meta_property, self).__init__(fget, fset, fdel, doc)

    def __get__(self, obj, type_):
        if self.key in obj.__dict__:
            return obj.__dict__[self.key]
        else:
            return super(meta_property, self).__get__(obj, type_)
