.. _configuration:

=============
Configuration
=============

There are several global settings with which you can configure the behavior of
this library. All settings use the prefix ``crud.``

.. _static_url_prefix:

Static View URL Prefix
----------------------

The application needs to serve static assets to display the default templates
properly (specifically, it uses `Bootstrap`_). These assets need their own
prefix to avoid routing conflicts with your other static files. Thus, this
setting allows you to define a custom prefix. By default, it is
``/static/crud`` which should be fine for most applications (as ``static`` is a
very common name, you can have all your CSS and JS files under this). However,
if this does not fit your use case, use this setting to change it.

If this is ``None``, no additional static view will be registered. This is
useful if you roll your own theme anyway (see :ref:`theming`) and you set up
your own static views for it.

+-----------------------------+
| Config File Setting Name    |
+=============================+
| ``crud.static_url_prefix``  |
+-----------------------------+

.. _Bootstrap: http://getbootstrap.com/
