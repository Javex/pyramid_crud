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
