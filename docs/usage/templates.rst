.. _templates:

=========
Templates
=========

Changing a Single Template
--------------------------

Changing a single template is as simple as copying it from the default theme
and adjusting it to your needs. For example, say you want to change the
``list.mako`` template. You copy it over and start editing.

.. code-block:: bash

    cp /path/to/pyramid_crud/templates/mako/bootstrap/list.mako my_library/templates/crud/list.mako

After you are done editing the template, you need to configure your view to
load it:

.. code-block:: python

    class MyCRUDView(CRUDView):
        ...
        template_list = 'crud/list.mako'

This is all assuming the ``crud`` directory can be looked up (in the example
above, you would need ``my_library/templates`` to be in ``mako.directories``).

For an explanation of each template and some additional details, see
:ref:`theming`.

.. _theming:

Create a Complete Theme
-----------------------

The default theme uses `Bootstrap`_ which looks nice but also not really
unique and does not integrate at all with your own application look. Thus, you
might want to roll your own look for all views. This is easily possible with
the :ref:`theme <theme_cfg>` configuration parameter.

.. _Bootstrap: http://getbootstrap.com/

.. note::
    This is an advanced technique. A lot of knowledge about the rest of the
    library is assumed throughout this section and so it is recommended
    that you make yourself familiar with the rest of the documentation before
    taking on own themes.

    It is perfectly okay to create your application with the default theme
    first and change it afterwards to your custom theme. This way you
    familiarize yourself with the library and have it much easier understanding
    what is going on here.

The best way to roll your own template is to copy the default template from
``pyramid_crud/templates/mako/bootstrap``. Let's say you want to create your
own theme by the name ``my_crud_theme``. First you copy over the theme folder:

.. code-block:: bash

    cp -a /path/to/pyramid_crud/templates/mako/bootstrap my_library/templates/my_crud_theme

Now you can directly enable your theme by configuring the
:ref:`theme <theme_cfg>` variable with the setting ``my_crud_theme`` (this is
assuming that this folder is in your ``mako.directories`` path). With this, you
should already have your new template enabled.

.. note::
    If you want to configure a default template, just create your own
    intermediate base class that defines the ``theme`` parameter. This isn't a
    very pythonic solution but it works and is very flexible.

Now you should fire up your text editor and take a look at the files in your
new theme folder. Here is a description of the files used:

.. note::
    Each file receives the usual ``request`` and ``view`` parameters pyramid
    passes in by default.

base.mako
    Contains the basic template with style sheets, flash messages and
    everything else that each template needs. You will define your own look
    here.

    If you already have your own template, you don't need this file and can
    delete it. You then have two options for configuring a custom base
    template:

    * You can statically set the path in each ``<%include`` statement in the
      inheriting templates or

    * You can define :ref:`template_base <template_override_cfg>` on the view
      and set it to the path of
      your own base template. It will then take this path as the base for all
      your templates and the regular base file is not needed anymore.

    If you roll your own base, pay attention to the flash messages and their
    queue names: They are currently statically configured and so you have to
    read these queues or won't see any messages at all.

    Also pay attention to the blocks used by inherting templates and either
    change them or define them in your base (e.g. ``head`` and ``heading``).

list.mako
    A simple list view. It gets two arguments: The ``items`` parameter is a
    query that you can iterate over to get the object instances for each row.
    The ``action_form`` parameter is a form instance with the following fields:

    action
        A select list where you can choose an action and execute it on multiple
        items at once (see :ref:`actions`).

    items
        A field that has one checkbox field for each item in the ``items``
        iterable. If you iterate over it, you get a single field that renders
        to a checkbox. In the default implementation, :func:`zip` is used to
        provide each loop iteration with a single checkbox field and the
        corresponding item.

    csrf_token
        A CSRF token field. This is required and must be displayed somewhere in
        the form or the validation will fail.

    submit
        A submit button that sends the form to execute the actions on the
        selected items.

edit.mako
    The view of a single item being edited. In the default implementation, this
    loads a fieldset for each configured fieldset on the form and then loads an
    inline template for each configured inline on the form. It receives the
    following parameters:

    form
        A form representing the item being edited. It is an instance of your
        subclassed :class:`ModelForm`. Look at the documentation for
        :ref:`forms` for more information on supported methods (make sure to
        also checkout linked documentation from there).

    is_new
        A boolean representing whether this is a new item or not.

delete_confirm.mako
    This template is invoked after the delete action was called and displays an
    intermediate view to make sure the user really wants to delete the selected
    items. It gets the following arguments:

    form
        The same form that the list view got as ``action_form``

    items
        The list of items to be deleted.

edit_inline/\*.mako
    Any file in this folder is considered an inline template to be included.
    The following parameters are given during inclusion:

    inline
        The class that is inlined (not an instance!). It is the subclass you
        made from base of :class:`BaseInLine <pyramid_crud.forms.BaseInLine>`.

    items
        Instances of the above ``inline`` parameter, each being a form to be
        displayed inlined.

fieldsets/\*.mako
    This file is used by the ``edit.mako`` template for each fieldset that
    should be rendered. It gets a single ``fieldset`` argument which is a dict
    with the following keys (note that it also keeps globals of the parent):

    title
        The title of this fieldset, usually displayed in a ``<legend>`` tag.

    fields
        A list of field names on the form. Use these to retrieve the correct
        field from the form instance. This is used instead of iterating over
        the form so you can group the fields into fieldsets.

You often don't need to edit all of the files if you don't use them. For
example, the ``grid`` fieldset is just a special case and can often go unused
(you can delete it if you never use it on any fieldset). You can also often
keep the default template if you like the way they do things and just style
them by creating your own stylesheet using the same classes bootstrap does.

Keeping Some Templates from the Default Library
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you might want to change the complete look and overwrite most of the
templates but keep some of them from the old library. You could just keep the
original copy you made above but that is not a good idea because you might miss
out on updates to the templates. You can abuse the ``template_*`` setting for
this, as it works both ways: Just set it to the path of the template you want
to keep. For example, to keep the ``delete_confirm`` template but overwrite
everything else, configure your view like this:

.. code-block:: python

    class MyCRUDView(CRUDView):
        ...
        template_delete_confirm = 'pyramid_crud:templates/mako/bootstrap/delete_confirm.mako'

Note how this is the full asset specification of the template because it is not
in any of the directories configured with ``mako.directories``. Also note, that
you cannot do this with templates in subdirectories (see
:ref:`template_* <template_override_cfg>` for an explanation and solution).

Supporting Different Template Engines
-------------------------------------

Supporting another template engine is very simple. Assuming you already use
them in the rest of the application, you have them set up anyway. Once you have
a theme for this engine, you can just set it to the file extension of this
theme.

Let's say, for example, you have created a `Chameleon`_ theme with all file
names ending in ``.pt``. If you have this renderer enabled properly, it will
automatically be chosen correctly, if you give pyramid a path to a file ending
with ``.pt``. Thus, in addition to configuring your theme (see above), you just
configure the :ref:`template_ext <template_ext_cfg>` parameter to ``.pt`` and
are good to go. This is what your view might look like:

.. code-block:: python

    class MyCRUDView(CRUDView)
        ...
        theme = 'templates/my_chameleon_theme'
        template_ext = '.pt'

Now assuming the lookup is correctly configured, this will fetch the templates
using the correct renderer.

.. _Chameleon: http://chameleon.readthedocs.org/en/latest/
