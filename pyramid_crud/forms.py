import wtforms_alchemy
import six
from wtforms.ext.csrf.form import SecureForm
import wtforms
from .util import get_pks, meta_property
from sqlalchemy.orm.session import object_session
from sqlalchemy.inspection import inspect
from webob.multidict import MultiDict
import logging
try:
    from collections import OrderedDict
except ImportError:  # pragma: no cover
    from ordereddict import OrderedDict


log = logging.getLogger(__name__)


class _CoreModelMeta(wtforms_alchemy.ModelFormMeta):
    """
    Metaclass for :class:`_CoreModelForm`. Assignes some class properties. Not
    to be used directly.
    """
    def __new__(meta, name, bases, attrs):
        # Copy over docstrings from parents
        def get_mro_classes(bases):
            return (mro_cls for base in bases for mro_cls in base.mro()
                    if mro_cls != object)
        if not('__doc__' in attrs and attrs['__doc__']):
            for mro_cls in get_mro_classes(bases):
                doc = mro_cls.__doc__
                if doc:
                    attrs['__doc__'] = doc
                    break
        for attr, attribute in attrs.items():
            if not attribute.__doc__:
                for mro_cls in (mro_cls for mro_cls in get_mro_classes(bases)
                                if hasattr(mro_cls, attr)):
                    doc = getattr(getattr(mro_cls, attr), '__doc__')
                    if doc:
                        attribute.__doc__ = doc
                        break
        return super(_CoreModelMeta, meta).__new__(meta, name, bases, attrs)

    @meta_property
    def title(cls):
        """See inline documentation for ModelForm"""
        return inspect(cls.Meta.model).class_.__name__

    @meta_property
    def title_plural(cls):
        """See inline documentation for ModelForm"""
        return cls.title + "s"

    @meta_property
    def name(cls):
        """See inline documentation for ModelForm"""
        return inspect(cls.Meta.model).class_.__name__.lower()

    @meta_property
    def field_names(cls):
        """
        A property on the class that returns a list of field names for the
        associated form.

        :return: A list of all names defined in the field in the same order as
            they are defined on the form.
        :rtype: list of str
        """
        return [field.name for field in cls()]


@six.add_metaclass(_CoreModelMeta)
class _CoreModelForm(wtforms_alchemy.ModelForm):
    """
    Base class for all complex form actions. This is used instead of the usual
    form class. Not to be used directly.
    """

    def __init__(self, formdata=None, obj=None, *args, **kw):
        self.obj = obj
        self.formdata = formdata
        super(_CoreModelForm, self).__init__(formdata, obj, *args, **kw)

    @property
    def primary_keys(self):
        """
        Get a list of pairs ``name, value`` of primary key names and their
        values on the current object.
        """
        if self.obj is None:
            raise AttributeError("No object attached")
        return [(pk, getattr(self.obj, pk, None))
                for pk in get_pks(self.Meta.model)]

    @property
    def fieldsets(self):
        """See inline documentation for ModelForm"""
        default_fields = [field.name for field in self
                          if field.name != 'csrf_token']
        return [{'title': '', 'fields': default_fields}]


class CSRFForm(SecureForm):
    """
    Base class from which new CSRF-protected forms are derived. Only use this
    if you want to create a form without the extra model-functionality, i.e.
    is normal form.

    If you want to create a CSRF-protected model form use
    :class:`CSRFModelForm`.
    """

    def generate_csrf_token(self, csrf_context):
        """
        Create a CSRF token from the given context (which is actually just a
        :class:`pyramid.request.Request` instance). This is automatically
        called during ``__init__``.
        """
        self.request = csrf_context
        return self.request.session.get_csrf_token()

    def validate(self):
        """
        Validate the form and with it the CSRF token. Logs a warning with the
        error message and the remote IP address in case of an invalid token.
        """
        result = super(CSRFForm, self).validate()
        if not result and self.csrf_token.errors:
            log.warn("Invalid CSRF token with error(s) '%s' from IP address "
                     "'%s'."
                     % (", ".join(self.csrf_token.errors),
                        self.request.client_addr))
        return result


class ModelMeta(_CoreModelMeta):
    def __new__(meta, name, bases, attrs):
        if "inlines" not in attrs:
            attrs["inlines"] = []
        return super(ModelMeta, meta).__new__(meta, name, bases, attrs)


@six.add_metaclass(ModelMeta)
class ModelForm(_CoreModelForm):
    """
    Base-class for all regular forms.

    The following configuration options are available on this form in addition
    to the full behavior described for `WTForms-Alchemy`_

    .. _WTForms-Alchemy: https://wtforms-alchemy.readthedocs.org

    .. note::

        While this class can easily be the base for each form you want to
        configure, it is strongly recommended to use the :class:`CSRFModelForm`
        instead. It is almost no different than this form except for a new
        ``csrf_token`` field. Thus it should never hurt to subclass it instead
        of this form.

    Meta
        This is the only mandatory argument. It is directly taken over from
        `WTForms-Alchemy`_ so you should check out their documentation on this
        class as it will provide you with a complete overview of what's
        possible here.

    .. _inlines:

    inlines
        A list of forms to use as inline forms. See :ref:`inline_forms`.

    .. _fieldsets:

    fieldsets
        Optionally define fieldsets to group your form into categories. It
        requires a list of dictionaries and in each dictionary, the following
        attributes can/must be set:

        * ``title``: A title to use for the fieldset. This is required but may
          be the empty string (then no title is displayed).

        * ``fields``: A list of field names that should be displayed together
          in a fieldset. This is required.

    title
        Set the title of your form. By default this returns the class name of
        the model. It is used in different places such as the title of the
        page.

    title_plural:
        The plural title. By default it is the title with an "s" appended,
        however, you somtimes might want to override it because "Childs" just
        looks stupid ;-)

    name:
        The name of this form. By default it uses the lowercase model class
        name. This is used internally und you normally do not need to change
        it.

    get_dbsession:
        Unfortunately, you have to define this ``classmethod`` on the form to
        get support for the unique validator. It is documented in
        `Unique Validator`_. This is a limitation we soon hope to overcome.
    """
    @classmethod
    def _relationship_key(self, other_form):
        """
        Get the name of the attribute that is the relationship between this
        forms model and the model defined on another form.

        By default the ``relationship_name`` attribute of ``other_form`` is
        looked up and used, if it is present. Otherwise, the relationship is
        determined dynamically.

        :param other_form: The other form to which the relationship should be
            found.
        """
        # If explicitly defined, return it
        if other_form.relationship_name:
            return other_form.relationship_name

        other_model = other_form.Meta.model
        candidates = []
        for relationship in inspect(self.Meta.model).relationships:
            if relationship.mapper.class_ == other_model:
                candidates.append(relationship.key)
        if len(candidates) == 0:
            raise TypeError("Could not find relationship between the models "
                            "%s and %s" % (self.Meta.model, other_model))
        elif len(candidates) > 1:
            raise TypeError("relationship between the models %s and %s is "
                            "ambigous. Please specify the "
                            "'relationship_name' attribute on %s"
                            % (self.Meta.model, other_model, other_form))
        return candidates[0]

    def process(self, formdata=None, obj=None, **kwargs):
        super(ModelForm, self).process(formdata, obj, **kwargs)
        self.process_inline(formdata, obj, **kwargs)

    def process_inline(self, formdata=None, obj=None, **kwargs):
        """
        Process all inline fields. This sets the global attribute
        ``inline_fields`` which is a dict-like object that contains as keys
        the name of all defined inline fields and as values a pair of
        ``inline, inline_forms`` where ``inline`` is the inline which the
        name refers to and ``inline_forms`` is the list of form instances
        associated with this inline.

        This list consists of pairs ``form, is_extra``, where ``form`` is just
        the form instance representing a single item and ``is_extra`` is a
        boolean that describes whether this field is already present in the
        database (in that case ``False``) or currently just an extra field
        that is not yet persisted (``True``).
        """
        self.inline_fieldsets = OrderedDict()
        for inline in self.inlines:
            inline_forms = []
            inline_formdata = {}
            if formdata:
                # create a dictionary of data by index for all existing form
                # fields. It basically parses back its pattern of assigned
                # names (i.e. inline.name_index_field.name).
                # The created values can then be sent to the individual forms
                # below based on their index.
                item_count = int(formdata.get('%s_count' % inline.name, 0))
                for index in range(item_count + 1):
                    inline_formdata[index] = MultiDict()
                    for field in inline.field_names:
                        data = formdata.get('%s_%d_%s' % (inline.name,
                                                          index, field))
                        if data:
                            inline_formdata[index][field] = data

            if formdata:
                count = formdata.get('%s_count' % inline.name)
            else:
                count = None

            # Delete items where requested
            to_delete = set()  # Which items should be deleted?
            if formdata and count is not None:
                count = int(count)
                for index in range(count):
                    delete_key = 'delete_%s_%d' % (inline.name, index)
                    if delete_key in formdata:
                        # Get the primary keys from the form and delete the
                        # item with the matching primary keys.
                        pks = inline.pks_from_formdata(formdata, index)
                        if pks:
                            session = object_session(obj)
                            target = session.query(inline.Meta.model).get(pks)
                            if target is None:
                                raise LookupError("Target with pks %s does "
                                                  "not exist" % str(pks))
                            session.delete(target)
                            # make sure the list is reloaded
                            session.expire(obj)
                            count -= 1
                        else:
                            to_delete.add(index)

            # Find the matching relationship
            # We determine this *outside* of the obj block because we want to
            # raise this on the user if there is a problem ASAP.
            key = self._relationship_key(inline)

            # Add all existing items
            if obj:
                index = -1  # Needed in case there are no items yet
                for index, item in enumerate(getattr(obj, key)):
                    form = inline(inline_formdata.get(index), item)
                    inline_forms.append((form, False))
                max_index = index + 1
            else:
                max_index = 0

            # Make the correct number of extra empty fields
            # If there currently is a count (only on POST request), we take the
            # value from the form, otherwise we use the configured default.
            # In case of POST, we have to subtract the existing database items
            # from above as those fields were already added.
            if count is None:
                extra = inline.extra
            else:
                extra = count - max_index
            if formdata and 'add_%s' % inline.name in formdata:
                extra += 1

            # Add empty form items
            for index in range(max_index, extra + max_index):
                # Only add an extra field if deletion of it was not requested
                if index not in to_delete:
                    form = inline(inline_formdata.get(index))
                    inline_forms.append((form, True))

            # For all forms, rename them and reassign their IDs as well. Only
            # by this measure can be guaranteed that each item can be addressed
            # individually.
            for index, (form, _) in enumerate(inline_forms):
                for field in form:
                    field.name = "%s_%d_%s" % (inline.name, index, field.name)
                    field.id = field.name

            self.inline_fieldsets[inline.name] = inline, inline_forms

    def populate_obj(self, obj):
        super(ModelForm, self).populate_obj(obj)
        self.populate_obj_inline(obj)

    def populate_obj_inline(self, obj):
        """
        Populate all inline objects. It takes the usual ``obj`` argument that
        is the **parent** of the inline fields. From these all other values
        are derived and finally the objects are updated.

        .. note::
            Right now this assumes the relationship operation is a ``append``,
            thus for example set collections won't work right now.
        """
        session = object_session(obj)
        for inline, forms in self.inline_fieldsets.values():
            inline_model = inline.Meta.model
            for index, (inline_form, _) in enumerate(forms):
                # Get the primary keys from the form. This ensures that we
                # update existing objects while new objects get inserted.
                pks = inline.pks_from_formdata(self.formdata, index)
                if pks is not None:
                    inline_obj = session.query(inline.Meta.model).get(pks)
                    if inline_obj is None:
                        raise LookupError("Target with pks %s does not exist"
                                          % str(pks))
                else:
                    inline_obj = inline_model()
                    relationship_key = self._relationship_key(inline)
                    getattr(obj, relationship_key).append(inline_obj)

                # Since the form was created like a standard form and the
                # object was loaded either from the database or newly created
                # and added to its associated object, we can now just populate
                # it as we would do with a normal form and object.
                inline_form.populate_obj(inline_obj)


@six.add_metaclass(_CoreModelMeta)
class BaseInLine(_CoreModelForm):
    """
    Base-class for all inline forms. You normally don't subclass from this
    directly unless you want to create a new inline type. However, all
    inline types share the attributes inherited by this template.

    Inline forms are forms that are not intended to be displayed by themselves
    but instead are added to the :ref:`inlines <inlines>` attribute of a normal
    form. They will then be displayed inside the normal form while editing,
    allowing for multiple instance to be added, deleted or modified at the same
    time. They are heavily inspired by Django's inline forms.

    An inline form is configurable with the following attributes, additionally
    to any attribute provided by `WTForms-Alchemy`_

    .. _WTForms-Alchemy: https://wtforms-alchemy.readthedocs.org

    Meta
        This is the standard `WTForms-Alchemy` attribute to configure the
        model. Check out their documentation for specific details.

    relationship_name
        The name of the *other side* of the relationship. Determined
        automatically, unless there are multiple relationships between the
        models in which case this must be overridden by the subclass.

        For example: If this is the child form to be inlined, the other side
        might be called ``children`` and this might be called ``parent`` (or
        it might not even exist, there is no need for a bidrectional
        relationship). The correct value would then be ``children`` *not*
        ``parent``.

    extra
        How many empty fields to display in which new objects can be added. Pay
        attention that often fields require intputs and thus extra field may
        often not be left empty. This is an intentional restriction to allow
        client-side validation without javascript. So only specify this if you
        are sure that items will always be added (note, however, that the extra
        attribute is not used to enforce a minimum number of members in the
        database). Defaults to ``0``.
    """
    extra = 0
    relationship_name = None

    @classmethod
    def pks_from_formdata(cls, formdata, index):
        """
        Get a list of primary key values in the order of the primary keys on
        the model. The returned value is suitable to be passed to
        :meth:`sqlalchemy.orm.query.Query.get`.

        :param formdata: A :class:`webob.multidict.MultiDict` that contains all
            parameters that were passed to the form.

        :param index: The index of the element for which the primary key is
            desired. From this, the correct field name to get from ``fromdata``
            is determined.
        :type index: int

        :return: A tuple of primary keys that uniquely identify the object in
            the database. The order is based on the order of primary keys in
            the table as reported by SQLAlchemy.
        :rtype: tuple
        """
        pks = []
        for pk in get_pks(cls.Meta.model):
            key = '%s_%d_%s' % (cls.name, index, pk)
            pk_val = formdata.get(key)
            if pk_val is None or pk_val == '':
                return
            pk_val = int(pk_val)
            pks.append(pk_val)
        return tuple(pks)


class TabularInLine(BaseInLine):
    """
    A base class for a tabular inline display. Each row is displayed in a
    table row with the field labels being displayed in the table head. This is
    basically a list view of the fields only that you can edit and delete them
    and even insert new ones.
    """
    template = 'default/edit_inline/tabular.mako'
    """The default template for tabular display"""


class CSRFModelForm(ModelForm, CSRFForm):
    """
    A form that adds a CSRF token to the form. Derive from this class for
    security critical operations (read: you want it most of the time and it
    doesn't hurt).

    Do not derive from this for inline stuff and other composite forms: Only
    the main form should use this as you only need one token per request.

    All configuration is done exactly in the same way as with the
    :class:`.ModelForm` except for one difference: An additional
    ``csrf_context`` argument is required. The pre-configured views and
    templates already know how to utilize this field and work fine with
    and without it.
    """
    # Developer Note: This form works through multiple inheritance. But the
    # CSRFForm is not a typical mixin, it derives from the Form class whereas
    # ModelForm also derives from it. As a result, Python's C3 implementation
    # resolves this a bit unintuitively. However, this actually saves as: The
    # calling goes up to the wtforms_alchemy.ModelForm but then, instead of
    # going to wtforms.Form, it goes to CSRFForm. Thus, as long as the parent
    # is always called with super() throughout the inheritance chain, this
    # works without needing to implement a custom __init__ that merges both
    # forms.


class MultiCheckboxField(wtforms.fields.SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.

    Example for displaying this field:

    .. code-block:: python

        class MyForm(Form):
            items = MultiCheckboxField(choices=[('1', 'Label')]
        form = MyForm()
        for item in form.items:
            str(item)  # the actual field to be displayed, likely in template

    If you don't iterate, it produces an unordered list be default (if ``str``
    is called on ``form.items``, not each item individually).

    And with formdata it might look like this:

    .. code-block:: python

        # Definition same as above
        formdata = MultiDict()
        formdata.add('items', '1')
        form = MyForm(formdata)
        assert form.items.data == ['1']

    As you can see, a list is produces instead of a scalar value which allows
    multiple fields with the same name.
    """
    widget = wtforms.widgets.ListWidget(prefix_label=False)
    option_widget = wtforms.widgets.CheckboxInput()

    def pre_validate(self, form):
        if not self.data:
            return
        values = list(c[0] for c in self.choices)
        msg = ('One of the selected items does not exist anymore. It has '
               'probably been deleted.')
        for d in self.data:
            if d not in values:
                raise ValueError(self.gettext(msg))


class MultiHiddenField(wtforms.fields.SelectMultipleField):
    """
    A field that represents a list of hidden input fields the same way as
    :class:`.MultiCheckboxField` and
    :class:`wtforms.fields.SelectMultipleField`.
    """
    widget = wtforms.widgets.HiddenInput()
    option_widget = wtforms.widgets.HiddenInput()

    def pre_validate(self, form):
        if not self.data:
            return
        values = list(c[0] for c in self.choices)
        msg = ('One of the selected items does not exist anymore. It has '
               'probably been deleted.')
        for d in self.data:
            if d not in values:
                raise ValueError(self.gettext(msg))


class SelectField(wtforms.fields.SelectField):
    """
    Same as :class:`wtforms.fields.SelectField` with a custom validation
    message and the requirement that ``data`` evaluates to ``True`` (for the
    purpose of having an empty field that is not allowed).
    """

    def pre_validate(self, form):
        for v, _ in self.choices:
            if self.data == v and self.data:
                break
        else:
            raise ValueError(self.gettext('Please select an action to be '
                                          'executed.'))
