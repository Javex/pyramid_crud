.. _views:

=====
Views
=====

Add a New View
--------------

Configuration
-------------

The main configuration of the library is done on the view. By subclassing
:class:`.CRUDView` for each new view you can create an individual configuration
that turns your model & form into a fully accessible CRUD interface. The
available confiugration parameters are described on the class:

.. module:: pyramid_crud.views

.. autoclass:: CRUDView

.. _view_configurator:

View & Route Setup
~~~~~~~~~~~~~~~~~~

Setting up views and routes is delegated to a special configurator class that
creates a route & view for each available view, i.e. list, edit, new and
delete. Since you often need to change the routes and views to match your
needs, you can subclass this and start overwriting its behavior. The interface
is very simple:

.. note::

    There is a slight overhead to configuring views like this because it
    requires the creation of an additional class. However, approaches like
    configuring parameters directly on the view are inflexible and setting
    awkward callables (in theory the most pythonic way) look ugly. Thus,
    this method is both flexible and easy to read.

.. autoclass:: ViewConfigurator

.. automethod:: ViewConfigurator.configure_list_view
.. automethod:: ViewConfigurator.configure_edit_view
.. automethod:: ViewConfigurator.configure_new_view

There are also some :ref:`helper methods <view_configurator_api>` available.

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

label
    This is taken over from WTForms-Alchemy but is used in more places. Instead
    of being just used as the label on a form, it is also used as a column
    heading in the list view. Each object should have one, but some functions
    set it (for example, the column header function associated with
    :ref:`list_display <list_display>` provides a default). For specific
    behavior on this
    regarding different views you should consult the associated documentation.
    While you should normally set it, not setting it will invent some hopefully
    nice-looking strings for the default usage (basically list and edit views).

description
    Used on form fields to describe a field more in-depth than a label can.
    This text may be arbitrarily long. It is not displayed on all templates
    (see :ref:`fieldset_templates`).

css_class
    A css class which should be set on this element's context. Currently this
    is only used for the list view where the ``th`` element gets this class so
    you can style your table based on individual columns. See the documentation
    on :ref:`list_display <list_display>` for more info.

bool
    This value is not always set, but when it is set, it indicates if this item
    is a boolean type. Currently this is only set for the list headings and
    there it is unused but can be adapted by custom templates.

func
    This is only used with actions and defines the callable which executes an
    action. It is part of the dict returned by ``_all_actions`` on the view.

API
---

The classes, methods and attributes described here are normally not used
directly by the user of the library and are just here for the sake of
completeness.

:class:`CRUDView`
~~~~~~~~~~~~~~~~~

The following methods refer to specific views:

.. automethod:: CRUDView.list
.. automethod:: CRUDView.delete
.. automethod:: CRUDView.edit

Addtionally, the following helper methods are used internally during several
sections of the library:

.. automethod:: CRUDView.redirect
.. automethod:: CRUDView.get_template_for
.. automethod:: CRUDView._get_request_pks
.. automethod:: CRUDView._get_route_pks
.. automethod:: CRUDView._edit_route
.. automethod:: CRUDView.iter_head_cols
.. automethod:: CRUDView.iter_list_cols

.. _view_configurator_api:

:class:`ViewConfigurator`
~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to the methods described above, the default implementation has a
few helper
methods. These are not required in any case since they are only called by the
above methods. However, since these methods are used to factor out common
tedious work, you might either use or override them and possibly not even touch
the default implementations above.

.. automethod:: ViewConfigurator._configure_view
.. automethod:: ViewConfigurator._configure_route
.. automethod:: ViewConfigurator._get_route_name
.. automethod:: ViewConfigurator._get_route_pks


