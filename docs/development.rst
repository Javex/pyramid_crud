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

Running tests is easily done:

.. code-block:: text

    python setup.py test

If you want more control over tests and develop your own, it is recommended to
install `py.test`_:

.. _py.test: http://pytest.org/latest/

.. code-block:: text

    pip install pytest

Then you can execute tests with:

.. code-block:: text

    py.test tests/

Now you can control the tests being executed and provide additional options
using the usual py.test command line.

Contributing
------------
