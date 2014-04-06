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

Button
~~~~~~

.. autoclass:: ButtonForm
    :members:
