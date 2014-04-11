.. _forms:

=====
Forms
=====

.. automodule:: pyramid_crud.forms

Add a New Form
--------------

Configuration
-------------

To configure a normal form, you subclass the :class:`.ModelForm`. On this
subclass there are several options you can/must override. The mandatory options
are listed first, followed by a list of optional configuration parameters.
Finally, you can of course always override the methods on the form.

.. autoclass:: ModelForm
    :members:
    :inherited-members:

.. _fieldset_templates:

Fieldset Templates
~~~~~~~~~~~~~~~~~~

You can configure custom fieldset templates on the :ref:`fieldsets <fieldsets>`
configuration parameter by setting the "template" key for a fieldset. The
following fieldsets are available:

horizontal
    A typical horizontal display that renders each form field in its own row
    with a label before the field.

grid
    A grid display that renders the field first and then displays the label.
    All fields are next to each other and line breaks only happen at the edge
    of the screen. This is a good template for a fieldset that consists only of
    checkboxes.

.. _inline_forms:

Inline Forms
------------

.. autoclass:: BaseInLine
    :members:
    :inherited-members:

.. autoclass:: TabularInLine

Extra Forms
-----------

CSRF
~~~~

The CSRF Forms are special forms to protect you against CSRF attacks. There are
two different types: The :class:`.CSRFForm` is the base for any form that
wants to enable CSRF and is not limited to the usage within the scope of this
library (it is not integrated with the rest of the system, it only implements
a WTForms form that takes a :class:`pyramid.request.Request` as the
``csrf_context``). The :class:`.CSRFModelForm` on the other hand *is*
integrated with the rest of the library and should be used to protect a form
against CSRF attacks while still maintaining the complete functionality of the
:class:`.ModelForm`.

.. autoclass:: CSRFForm
    :members:

.. autoclass:: CSRFModelForm
    :members:


API
---

.. autoclass:: MultiCheckboxField
.. autoclass:: MultiHiddenField
.. autoclass:: SelectField

.. _Unique Validator: https://wtforms-alchemy.readthedocs.org/en/latest/validators.html#unique-validator
