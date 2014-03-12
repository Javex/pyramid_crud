def get_pks(model):
    """
    Get a list of primary key names for a given SQLAlchemy model.
    """
    return [pk.name for pk in model.__table__.primary_key.columns]


def classproperty(func):
    """
    A decorator to turn a method into a property on a class. Behaves the same
    as a :cls:`property` only for classes instead of instances.
    """

    class ClassPropertyDescriptor(object):

        def __init__(self, fget, fset=None):
            self.fget = fget
            self.fset = fset

        def __get__(self, obj, klass=None):
            if klass is None:
                klass = type(obj)
            return self.fget.__get__(obj, klass)()

        def __set__(self, obj, value):
            if not self.fset:
                raise AttributeError("can't set attribute")
            type_ = type(obj)
            return self.fset.__get__(obj, type_)(value)

        def setter(self, func):
            if not isinstance(func, (classmethod, staticmethod)):
                func = classmethod(func)
            self.fset = func
            return self

    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)
