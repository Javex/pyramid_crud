pyramid_crud
============

This software is a framework with the attempt to replicate a behavior similar
to Django's [Generic Views](https://docs.djangoproject.com/en/1.6/ref/class-based-views/generic-display/)
and [Admin Pages](https://docs.djangoproject.com/en/1.6/ref/contrib/admin/).

It aims to provide a simple yet configurable interface to get a CRUD (Create,
Read, Update, Delete) interface on persisted data.

This library is an **unofficial** extension to Pyramid. This is not likely to
change unless the libraries dependencies are decoupled as described below.

**Note**: This library is in an early phase and contributions are welcome that
fix bugs or add missing features. Just please make sure to keep it as clean as
possible. Also always take a look at how Django achieves the desired
functionality (if present), because they have some good ideas on keeping the
code clean and readable.

Dependencies
============

It currently relies on

- [Pyramid](http://docs.pylonsproject.org/en/latest/docs/pyramid.html)
- [WTForms](http://wtforms.readthedocs.org/)
- [SQLAlchemy](docs.sqlalchemy.org)
- [WTForms-Alchemy](https://wtforms-alchemy.readthedocs.org/en/latest/)
- [Mako](docs.makotemplates.org)

The Mako integration is very loose, allowing for arbitrary templates to be used
as long as they are registered properly with Pyramid.

WTForms on the other hand is more tightly integrated. It should be easily
possible to write an adapter that replicates the WTForms interface and allows
integration with other form libraries but this library was not designed for it.
However, I am happy to accept pull requests that change this behavior to allow
arbitrary form libraries as long as the code stays clean and the interface
does not require major changes.

SQLAlchemy is also very tightly bound to the library. Both the form and the
view part rely on SQLAlchemy and its interface. However, seeing as SQLAlchemy
is basically _the_ go-to ORM outside of Django, I don't see a need except if
NoSQL databases are desired.

Pyramid is, of course, at the core of this library and there are currently no
plans to decouple it to allow arbitrary frameworks the usage of this library.
Again, I accept pull requests for this, but I find it much more likely that a
split into a new library that provides this functionality independent of a web
framework and separate integration into different is the way to go if this is
desired. If you want to work on something like this, please contact me, so we
can coordinate on this.
