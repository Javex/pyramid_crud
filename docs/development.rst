Development
===========

Building Documentation
----------------------

To build the documentation you first need to install all documentation
dependencies:

.. code-block:: text

    pip install -r docs_require.txt

Then you can build the documentation:

.. code-block:: text

    python setup.py build_sphinx


Running Tests
-------------

Before you can run tests, you need to install the requirements. These consist
of the requirements to create docs (for doctests) and pytest:

.. code-block:: text

    pip install -r tests_require.txt

.. note::
    ``mock`` is an unnecessary requirement for users of python 3.3 and above,
    but it is included in the above file unconditionally.

Now you can run your tests with:

.. code-block:: text

    python setup.py test

If you need more control over which tests are executed, you can also execute
pytest and doctest directly:

.. code-block:: text

    py.test tests/
    make -C docs/ doctest

.. note::

    Our tests are also run against templates. However, as they are not python
    files, the test suite automatically compiles them into a temporary
    directory. This directory should never be checked into GitHub and also be
    removed before installing the library (it does not hurt, it just pollutes
    the directory).

    Running tests against templates also is included in coverage (the reason
    why we need an accessible template module directory). The coverage values
    are reported by Travis CI to coveralls. However, since the code for this is
    not on GitHub, you cannot see which lines were missted online. Instead, you
    need to run those tests locally and get coverage output with ``coverage
    html`` after you have run the tests.

Contributing
------------
