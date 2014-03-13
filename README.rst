pyramid_crud
============

|BuildStatus| |CoverageStatus| |LatestVersion| |License|

This software is a framework with the attempt to replicate a behavior similar
to Django's `Generic Views`_
and `Admin Pages`_.

.. _Generic Views: https://docs.djangoproject.com/en/1.6/ref/class-based-views/generic-display/
.. _Admin Pages: https://docs.djangoproject.com/en/1.6/ref/contrib/admin/

It aims to provide a simple yet configurable interface to get a CRUD (Create,
Read, Update, Delete) interface on persisted data.

This library is an **unofficial** extension to Pyramid. This is not likely to
change unless the libraries dependencies are decoupled as described in
`A Word on Dependencies`_.

.. _A Word on Dependencies: https://pyramid-crud.readthedocs.org/en/latest/introduction.html#a-word-on-dependencies


.. note:: 
    This library is in an early phase and contributions are welcome that
    fix bugs or add missing features. Just please make sure to keep it as clean
    as possible. Also always take a look at how Django achieves the desired
    functionality (if present), because they have some good ideas on keeping
    the code clean and readable.

Links
-----

* `Documentation <http://pyramid-crud.readthedocs.org>`_
* `Source Code <https://github.com/Javex/pyramid_crud>`_
* `Package on PyPI <https://pypi.python.org/pypi/pyramid_crud>`_

.. |BuildStatus| image:: https://travis-ci.org/Javex/pyramid_crud.png?branch=master
   :target: https://travis-ci.org/Javex/pyramid_crud
   :alt: Build Status

.. |CoverageStatus| image:: https://coveralls.io/repos/Javex/pyramid_crud/badge.png
   :target: https://coveralls.io/r/Javex/pyramid_crud
   :alt: Coverage

.. |LatestVersion| image:: https://pypip.in/v/pyramid_crud/badge.png
   :target: https://pypi.python.org/pypi/pyramid_crud/
   :alt: Latest Version

.. |License| image:: https://pypip.in/license/pyramid_crud/badge.png
    :target: https://pypi.python.org/pypi/pyramid_crud/
    :alt: License
