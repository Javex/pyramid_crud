.. _actions:

=======================
Adding Actions to Forms
=======================

Similar to Django's `Admin actions`_, pyramid_crud also provides a way to
configure specific actions.

.. _Admin actions: https://docs.djangoproject.com/en/1.6/ref/contrib/admin/actions/

Introduction
------------

What are actions?
~~~~~~~~~~~~~~~~~

An action in the context of this library is something you perform on a list of
items that might change their state (or perform anything else, really). A
good example would be publishing multiple articles at once or activating
multiple users.

How do you configure actions?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Actions are configured by setting the :ref:`actions <actions_cfg>` parameter on
your
view. Possible values here are strings or callables. If a string is provided,
a method of the same name is looked up on the view and used as the callable.

Each callable gets two arguments: The view and the query which selects the
items for which the actions should be performed. Note that a query is used
instead of a list of items so that you can refine it or directly perform
actions on it. If you need a list, call ``.all`` on it or iterate over it.

So how do I create an action exactly?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's work by example and take the same example Django does so we can directly
see similarities and differences. Here's our definition with which we start:

.. code-block:: python

    class Article(Base):
        id = Column(Integer, primary_key=True)
        title = Column(Text)
        body = Column(Text)
        status = Column(Enum('p', 'd', 'w'))

        def __unicode__(self):
            return self.title

Now that we have our model, let's make a method to publish multiple articles at
once:

.. code-block:: python

    def make_published(view, query):
        query.update({'status': 'p'})
        return True, None

Notice, how we don't pass in the request as it can be accessed with
``view.request``. The view is an instance of your subclassed
:class:`CRUDView <pyramid_crud.views.CRUDView>`. The query is an instance of
:class:`Query <sqlalchemy.orm.query.Query>`. Additionally, you can see that
we return a pair here. The first value indicates success of the operation, the
latter value is an optional response (see :ref:`action_return` for a detailed
explanation).

Now you might want to have a nicer title than 'Make Published' (this title is
assigned by default, replacing underscores with spaces and calling
:meth:`str.title` on the result). To achieve a custom title (that will appear
in the list of items), assign a label to its :ref:`info dict <info_dict>`:

.. code-block:: python

    def make_published(view, query):
        query.update({'status': 'p'})
        return True, None
    make_published.info = {'label': "Mark selected stories as published"}

And how do I add it to a view?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

That's easy. Here is a full configuration based on the model above:

.. code-block:: python

    class ArticleForm(ModelForm):
        class Meta:
            model = Article

    class ArticleView(CRUDView):
        Form = ArticleForm
        url_path = '/articles'
        actions = [make_published]

See how we added the :ref:`actions <actions_cfg>` configuration directive? We
gave it a list (with one item) of actions that should be available on this
model.

And that's it, now you have an additional action available at your disposal.
Read on for some more information, including advanced techniques,
differences and what's missing in comparison to Django.

Advanced Techniques
-------------------

Handling Errors
~~~~~~~~~~~~~~~

To handle exceptions, wrap your code in a ``try-except-else`` clause.
You can then handle any exception and possibly log error
messages and flash a message to the user. This allows you to shield the user
from any application crashes and gives you the ability to examine the log for
the cause of the error.

Nonetheless, you can still raise exceptions and they will be passed through in
which case the section on :ref:`action_return` does not really apply (as no
value is returned).

An example of an implementation that shields to user from exceptions might look
like this:

.. code-block:: python

    def make_published(view, query):
        try:
            query.update({'status': 'p'})
        except:
            log.error("An error oucurred:\n%s" % format_traceback())
            self.request.session.flash("An error happened while publishing "
                                       "the article(s)")
            return False, None
        else:
            return True, None

This will inform the user of any failure and log the exact exception so you can
investigate the problem. Note that with a perfect implementation, you would
probably want to explicitly catch all possible exceptions and not use a
catch-all. However, since this implementation doesn't just ignore and instead
log the exception, it is not too bad to have a catch all here.

.. _action_return:

Returning Values From Actions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As already noted above, it is recommended to wrap your code in
``try-except-else`` blocks and return the status as a boolean. The reason for
this is to allow explicit changes in application behavior based on the result
of your execution.

You always have to return a pair of ``(success, response)`` to indicate how you
would like to proceed.

``success`` must be a boolean value. If it is ``False`` it indicates that the
action was not successful. In this case the redirect is **raised** which means
it is considered an exception. Any optional transaction (e.g. `pyramid_tm`_)
will see this exception and abort the transaction. Afterwards the page is
redirected. The ``response`` value is not used in this case, so it should
always be ``None``.

.. _pyramid_tm: http://docs.pylonsproject.org/projects/pyramid_tm/en/latest/

If ``success`` is ``True``, it is assumed that the action was successful. In
this case the redirect is **returned** and the transaction is committed. Note
that this is a fine distinction between success and failure and the user does
not see a difference (except error messages you might give out).

However, in the case of a successful response, you might also want to change
the returned value into something else (maybe redirect somewhere else or return
a whole new response). This can be done by setting the ``response`` paramater
which can really be anything that is allowed to be returned from a view.

So for example if you wanted to direct to a completely different page, you
could return an instance of
:class:`HTTPFound <pyramid.httpexceptions.HTTPFound>` that achieves this. On
the other hand, you maybe want to create an intermediate response. In that
case, you just need to return an instance of
:class:`Response <pyramid.response.Response>`. You could create this by calling
:func:`render_to_response <pyramid.renderers.render_to_response>` if you want
to render an intermediary view from a template. This is the technique the
delete action uses.

.. note::
    
    The more complex it gets, the more likely it is that a redirect to an
    actual view is much better than manually rendering or building your
    response. This allows you to factor out the code from your action into a
    separate view but has the drawback of an additional redirect and the need
    to keep all the formdata alive (e.g. in the session).

Actions as Methods on the View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of having an external function, you can add your action directly
to the view (in most cases the recommended way). For this, you just create a
method on the view instead of a function:

.. code-block:: python

    class ArticleView(CRUDView):
        ...
        def make_published(self, query):
            try:
                query.update({'status': 'p'})
            except:
                return False, None
            else:
                return True, None
        make_published = {'info': "Mark selected stories as published"}

Note how we renamed ``view`` to ``self`` because as a method the view reference
is now actually the own instance.

Instead of providing the action as a callable, you now use a string instead:

.. code-block:: python

    class ArticleView(CRUDView):
        actions = ['make_published']

This will look up the action as a method on the view and call it in the same
manner.

Currently Unspported Features from Django
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Site-wide actions: Currently it is not possible to add actions that are
  globally available. However, you can work around that by creating a custom
  subclass and modifiying the action list in the children during runtime,
  however, this is an unspported as of now and you might face some issues with
  mutability.

* Disabling actions: This is currently not supported at all.

* Runtime disabling/enabling of actions: While unspported, this is possible by
  overriding the ``_all_actions`` atribute. In the default implementation it
  behaves like a property but caches its result (using
  Pyramid's `reify <http://docs.pylonsproject.org/projects/pyramid/en/latest/api/decorator.html#pyramid.decorator.reify>`_
  decoartor). Take a look at the default implementation to see the format of
  the returned value.
