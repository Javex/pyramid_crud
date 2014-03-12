.. _introduction:

============
Introduction
============

Installation
------------

You can install ``pyramid_crud`` using pip:

.. code-block:: text
    
    pip install pyramid_crud

Or you can fetch the current sources and install it manually:

.. code-block:: text

    git clone https://github.com/Javex/pyramid_crud
    cd pyramid_crud
    python setup.py install

.. _dependencies:

A Word on Dependencies
----------------------

This library currently relies on certain other libraries. Therefore, it only
supports a certain use-case (or at least only integrates well there). Thus, if
your application stack differs from the libraries listed below, make sure to
read this section to see which parts can be changed and which cannot.

- `Pyramid <http://docs.pylonsproject.org/en/latest/docs/pyramid.html>`_
- `WTForms <http://wtforms.readthedocs.org/>`_
- `SQLAlchemy <http://docs.sqlalchemy.org/en/rel_0_9/>`_
- `WTForms-Alchemy <https://wtforms-alchemy.readthedocs.org/en/latest/>`_
- `Mako <http://docs.makotemplates.org/en/latest/>`_

The Mako integration is very loose, allowing for arbitrary templates to be used
as long as they are registered properly with Pyramid.

WTForms on the other hand is more tightly integrated. It should be easily
possible to write an adapter that replicates the WTForms interface and allows
integration with other form libraries but this library was not designed for it.
However, I am happy to accept pull requests that change this behavior to allow
arbitrary form libraries as long as the code stays clean and the interface
does not require major changes. Finally, there is no requirement for you to use
WTForms in the rest of your application: You can simply rely on WTForms only
for this library. As long as you don't deviate from the default mechanisms you
will not even have to concern yourself with WTForms at all.

SQLAlchemy is also very tightly bound to the library. Both the form and the
view part rely on SQLAlchemy and its interface. However, seeing as SQLAlchemy
is basically *the* go-to ORM outside of Django, I don't see a need except if
NoSQL databases are desired.

Pyramid is, of course, at the core of this library and there are currently no
plans to decouple it to allow arbitrary frameworks the usage of this library.
Again, I accept pull requests for this, but I find it much more likely that a
split into a new library that provides this functionality independent of a web
framework and separate integration into different frameworks is the way to go
if this is desired. If you want to work on something like this, please contact
me, so we can coordinate on this.

.. _quickstart:

QuickStart
----------

For this quickstart we assume you already have an application with models that
you want to enable CRUD for.

First you have to include ``pyramid_crud`` in your ``.ini`` file:

.. code-block:: ini
    
    pyramid.includes =
        ...
        pyramid_crud
        ...


.. code-block:: python

    from pyramid_crud.forms import CSRFModelForm
    from pyramid_crud.views import CRUDView
    from .models import MyModel


    class MyModelForm(CSRFModelForm):
        class Meta:
            model = MyModel

    class MyModelView(CRUDView):
        form = MyModelForm
        url_path = '/mymodel'

That gets you started: We create a form and a set of views for our form. Now
start your application and visit the application on the path ``/mymodel``. You
should see a list of present instances and also buttons to delete them and add
new instances. Finally, you can also click the first columns element to edit
an item. Go ahead, play around with it. Afterwards, you can head to
:ref:`usage` and start configuring the associated parts to behave the way you
need it to.
