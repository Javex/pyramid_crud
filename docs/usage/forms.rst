.. _forms:

=====
Forms
=====

Add a New Form
--------------

Configuration
-------------

The :class:`.BaseModelForm` provides you with several options to configure its
behavior:

``BaseModelForm.fieldsets``
###########################

Define fieldsets to group your form into categories. ``fieldsets`` is a list of
pairs ``(title, options)`` where ``title`` is the title that should be used for
each fieldset and ``options`` is a dict with the following elements:

* ``fields``: A list of field names that should be displayed together in a
  fieldset. *Required*.

Inline Forms
------------

``BaseInLine.relationship_name``
################################

The name of the relationship to inline. Determined automatically, unless there
are multiple relationships between the models in which case this must be
overwritten by the subclass.

``BaseInLine.extra``
####################

How many empty fields to display in which new objects can be added. Pay
attention that often fields require intputs and thus extra field may often not
be left empty. This is an intentional restriction to allow client-side
validation without javascript. So only specify this if you are sure that
items will always be added (note, however, that the extra attribute is not
used to enforce a minimum number of members in the database). Defaults to
``0``.

Extra Forms
-----------

CSRF
####

Button
######

API
---

.. automodule:: pyramid_crud.forms

.. autoclass:: BaseModelForm
    :members:

.. autoclass:: BaseInLine
    :members:

.. autoclass:: TabularInLine
    :members:

.. autoclass:: CSRFForm
    :members:

.. autoclass:: CSRFModelForm
    :members:

.. autoclass:: ButtonForm
    :members:
