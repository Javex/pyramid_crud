.. _views:

=====
Views
=====

Add a New View
--------------

Configuration
-------------

.. _info_dict:

The Info Dictionary
~~~~~~~~~~~~~~~~~~~

Each object can have an optional info dictionary attached (and in most cases
you will want one). The idea is based on the idea of `WTForms-Alchemy's Form
Customization`_ and actually just extends it. Several attributes used by this
library support inclusion of extra information in this dict. The following
options can be set and/or read and some are automatically defined if you do not
provide a value. The follwoing values are available:

.. _WTForms-Alchemy's Form Customization: https://wtforms-alchemy.readthedocs.org/en/latest/customization.html

``label``
    This is taken over from WTForms-Alchemy but is used in more places. Instead
    of being just used as the label on a form, it is also used as a column
    heading in the list view. Each object should have one, but some functions
    set it (for example, the column header function associated with
    :ref:`list_display <list_display>` provides a default). For specific
    behavior on this
    regarding different views you should consult the associated documentation.
    While you should normally set it, not setting it will invent some hopefully
    nice-looking strings for the default usage (basically list and edit views).

``css_class``
    A css class which should be set on this element's context. Currently this
    is only used for the list view where the ``th`` element gets this class so
    you can style your table based on individual columns. See the documentation
    on :ref:`list_display <list_display>` for more info.

``bool``
    This value is not always set, but when it is set, it indicates if this item
    is a boolean type. Currently this is only set for the list headings and
    there it is unused but can be adapted by custom templates.
        

API
---

.. automodule:: pyramid_crud.views

.. autoclass:: CRUDView
    :members:
