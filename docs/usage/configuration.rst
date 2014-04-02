.. _configuration:

=============
Configuration
=============

There are several global settings with which you can configure the behavior of
this library. All settings use the prefix ``crud.``

.. _template_renderer:

Template Renderer
-----------------

This setting specifies the template renderer to use or if none should be used.
It supports the following settings:

* ``mako`` to use the `Mako`_ templates provided with this library. This
  is the default.
* ``None`` if no default templates should be used. Use this if you want to
  completely roll your own templates.

.. _Mako: http://www.makotemplates.org/ 

In essence, this setting sets up additional lookup paths for the templates and
adds a configurable static view for CSS files etc (see
:ref:`static_url_prefix`)

+-----------------------------+
| Config File Setting Name    |
+=============================+
| ``crud.template_renderer``  |
+-----------------------------+

.. _static_url_prefix:

Static View URL Prefix
----------------------

The application needs to serve static assets to display the default templates
properly (specifically, it uses `Bootstrap`_). These assets need their own
prefix to avoid routing conflicts with your other static files. Thus, this
setting allows you to define a custom prefix. By default, it is
``/static/crud`` which should be fine for most applications (as ``static`` is a
very commong name, you can have all your CSS and JS files under this). However,
if this does not fit your use case, use this setting to change it. Note that it
only takes effect when using the templates provided with the library
(see :ref:`template_renderer`).

+-----------------------------+
| Config File Setting Name    |
+=============================+
| ``crud.static_url_prefix``  |
+-----------------------------+

.. _Bootstrap: http://getbootstrap.com/
