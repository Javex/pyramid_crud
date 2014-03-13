from wtforms_alchemy import model_form_factory
from wtforms.ext.csrf.form import SecureForm
from wtforms.fields import SubmitField
from wtforms.form import Form
from .util import classproperty, get_pks
from sqlalchemy.orm.session import object_session
from sqlalchemy.inspection import inspect
from webob.multidict import MultiDict
import logging
try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict


log = logging.getLogger(__name__)


class BaseModelForm(Form):
    """
    Base class for all complex form actions. This is used instead of the usual
    form class.
    """
    inlines = []

    def __init__(self, formdata=None, obj=None, *args, **kw):
        self.obj = obj
        self.formdata = formdata
        Form.__init__(self, formdata, obj, *args, **kw)

    @property
    def fieldsets(self):
        return [(None, {'fields': [field.name for field in self]})]

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
            raise ValueError("Could not find relationship between the models "
                             "%s and %s" % (self.Meta.model, other_model))
        elif len(candidates) > 1:
            raise ValueError("relationship between the models %s and %s is "
                             "ambigous. Please specify the "
                             "'relationship_name' attribute on %s"
                             % (self.Meta.model, other_model, other_form))
        return candidates[0]

    def process(self, formdata=None, obj=None, **kwargs):
        Form.process(self, formdata, obj, **kwargs)
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

            # Find the matching relationship
            key = self._relationship_key(inline)
            if key is None:
                raise ValueError("Could not find relationship for %s" % inline)

            # Add all existing items
            if obj:
                index = -1  # Needed in case there are no items yet
                for index, item in enumerate(getattr(obj, key)):
                    if 'delete_%s_%d' % (inline.name, index) in formdata:
                        # Get the primary keys from the form and delete the
                        # item with the matching primary keys.
                        pks = inline.pks_from_formdata(formdata, index)
                        if pks:
                            session = object_session(obj)
                            target = session.query(inline.Meta.model).get(pks)
                            object_session(target).delete(target)
                    else:
                        form = inline.form(inline_formdata.get(index), item)
                        inline_forms.append((form, False))
                max_index = index + 1
            else:
                max_index = 0

            # Make the correct number of extra empty fields
            # If there currently is a count (only on POST request), we take the
            # value from the form, otherwise we use the configured default.
            # In case of POST, we have to subtract the existing database items
            # from above as those fields were already added.
            count = formdata.get('%s_count' % inline.name)
            if count is None:
                extra = inline.extra
            else:
                extra = int(count) - max_index
            if 'add_%s' % inline.name in formdata:
                extra += 1

            # Add empty form items
            for index in range(max_index, extra + max_index):
                if 'delete_%s_%d' % (inline.name, index) not in formdata:
                    form = inline.form(inline_formdata.get(index))
                    inline_forms.append((form, True))

            # For all forms, rename them and reassign their IDs as well. Only
            # by this measure can be guarantee that each item can be addressed
            # individually.
            for index, (form, _) in enumerate(inline_forms):
                for field in form:
                    field.name = "%s_%d_%s" % (inline.name, index, field.name)
                    field.id = field.name

            self.inline_fieldsets[inline.name] = inline, inline_forms

    def populate_obj(self, obj):
        Form.populate_obj(self, obj)
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
        for inline in self.inlines:
            _, forms = self.inline_fieldsets[inline.name]
            inline_model = inline.Meta.model
            for index, (form, _) in enumerate(forms):
                # Get the primary keys from the form. This ensures that we
                # update existing objects while new objects get inserted.
                pks = inline.pks_from_formdata(self.formdata, index)
                session = object_session(obj)
                if pks is not None:
                    inline_obj = session.query(inline.Meta.model).get(pks)
                else:
                    inline_obj = inline_model()
                    relationship_key = self._relationship_key(inline)
                    getattr(obj, relationship_key).append(inline_obj)

                # Since the form was created like a standard form and the
                # object was loaded either from the database or newly created
                # and added to its associated object, we can now just populate
                # it as we would do with a normal form and object.
                form.populate_obj(inline_obj)

    @property
    def primary_keys(self):
        """
        Get a list of pairs ``name, value`` of primary key names and their
        values on the current object.
        """
        return [(pk, getattr(self.obj, pk, None))
                for pk in get_pks(self.Meta.model)]


class BaseInLine(object):
    extra = 0
    relationship_name = None

    @classproperty
    def title(self):
        """
        The title. By default this returns the class name of the model. It is
        used in different places such as the title of the page.
        """
        return inspect(self.Meta.model).class_.__name__

    @classproperty
    def title_plural(self):
        """
        The plural title. By default it is the title with an "s" appended.
        """
        return self.title + "s"

    @classproperty
    def name(self):
        """
        The name of this inline. By default it uses the lowercase model class
        name.
        """
        return inspect(self.Meta.model).class_.__name__.lower()

    @classproperty
    def form(self):
        """
        The form associated with this class. By default this creates a new type
        dynamically but this can be overwritten by subclasses to just return
        an actual class defined otherwise.
        """
        return type('%sInlineForm' % self.name,
                    (ModelForm,), {'Meta': self.Meta})

    @classproperty
    def field_names(self):
        """
        A :class:`.classproperty` that returns a list of field names for the
        associated form.

        :return: A list of all names defined in the field in the same order as
            they are defined on the form.
        :rtype: list of str
        """
        return [field.name for field in self.form()]

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
        result = SecureForm.validate(self)
        if not result and self.csrf_token.errors:
            log.warn("Invalid CSRF token with error(s) '%s' from IP address "
                     "'%s'."
                     % (", ".join(self.csrf_token.errors),
                        self.request.client_addr))
        return result


ModelForm = model_form_factory(BaseModelForm)
"""The base class for all non-critical forms and subforms."""


class CSRFModelForm(ModelForm, CSRFForm):
    """
    A form that adds a CSRF token to the form. Derive from this class for
    security critical operations (read: you want it most of the time and it
    doesn't hurt.

    Do not derive from this for inline stuff and other composite forms: Only
    the main form should use this as you only need one token per request.
    """
    def __init__(self, formdata=None, obj=None, csrf_context=None, *args,
                 **kwargs):
        ModelForm.__init__(self, formdata, obj, *args, **kwargs)
        self.csrf_token.current_token = self.generate_csrf_token(csrf_context)


class ButtonForm(CSRFForm):
    """
    A simple form that only includes a ``button`` and a ``csrf_token`` field.
    This can be used for operations on a form that should be single-click (like
    deletion or toggling a boolean value). Note that the reason for not using
    a URL for this is CSRF protection for these operations.

    The form is created in the usual way but accepts a single new argument
    ``title`` which is stored as the label's text on the form. Thus, you can
    instantiate this form many times with different titles.

    .. note::
        This form alone does not identify an item, you have to do that with the
        POST url you send the form to. If you were to include a button multiple
        rows in a single form, you would not be able to identify the correct
        object on the server side.

    An example of its usage can be found in the ``delete_form`` of the default
    :class:`.views.CRUDView` and the corresponding templates (e.g.
    ``default/list.mako``).
    """

    button = SubmitField()

    def __init__(self, formdata=None, obj=None, prefix='',
                 csrf_context=None, title=None, **kwargs):
        CSRFForm.__init__(self, formdata, obj, prefix, csrf_context, **kwargs)
        self.button.label.text = title
