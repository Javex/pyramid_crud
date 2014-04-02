from pyramid.httpexceptions import HTTPFound
import venusian
import six
import logging
from functools import partial
from .util import get_pks
from .forms import ButtonForm
from sqlalchemy import inspect
try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict


log = logging.getLogger(__name__)


class CRUDCreator(type):
    """
    Metaclass for :class:`CRUDView` to handle automatically registering views
    for new subclasses.
    """

    def __init__(cls, name, bases, attrs):
        def cb(context, name, ob):
            config = context.config.with_package(info.module)
            config.add_route(cls.route_name('list'),
                             '%s' % cls.url_path)
            config.add_view(cls, attr='list',
                            route_name=cls.route_name('list'),
                            renderer=cls._template_for('list'),
                            request_method='GET')

            config.add_route(cls.route_name('new'),
                             '%s/new' % cls.url_path)
            config.add_view(cls, attr='edit', route_name=cls.route_name('new'),
                            renderer=cls._template_for('edit'))
            pks = ",".join('{%s}' % pk_name
                           for pk_name in get_pks(cls.form.Meta.model))
            config.add_route(cls.route_name('edit'),
                             '%s/%s' % (cls.url_path, pks))
            config.add_view(cls, attr='edit',
                            route_name=cls.route_name('edit'),
                            renderer=cls._template_for('edit'))

            config.add_route(cls.route_name('delete'),
                             '%s/delete/%s' % (cls.url_path, pks))
            config.add_view(cls, attr='delete',
                            route_name=cls.route_name('delete'),
                            request_method='POST')
        if '__abstract__' not in attrs:
            have_attrs = set(attrs)
            need_attrs = set(('Form', 'url_path'))
            if have_attrs & need_attrs != need_attrs:
                missing = need_attrs - (have_attrs & need_attrs)
                raise AttributeError(
                    "Invalid configuration. The following attributes are "
                    "missing and need to be defined for a complete "
                    "configuration : %s" % ", ".join(missing))
            info = venusian.attach(cls, cb)


@six.add_metaclass(CRUDCreator)
class CRUDView(object):
    """
    The base class for all views. Views directly or indirectly subclassed from
    this define actual views (or intermediate base classes, if ``__abstract__``
    is ``True``).

    The following attributes can be defined to override behavior of the view:

    ``Form``: Mandatory argument that specifies the form class for which this
    view should be created. This must be a form as described in :ref:`forms`.

    ``url_path``: Mandatory argument for defining the base path under which
    this view should be available.

    ``dbsession``: Return the current SQLAlchemy session. By default this
    expects a ``dbsession`` attribute on the ``request`` object. It is
    **mandatory** that you either attach the attribute using an event
    or override this attribute (you can use a :class:`property` if you
    like).

    ``title``: The title of the view. By default it uses the name of the model
    class.

    ``title_plural``: The title when used in plural. By default this attached
    an "s" to the ``title``.

    ``template_dir``: The directory where to find templates. The default
    templates are provided in the ``default`` folder.

    ``template_ext``: Which file extension to use for templates. By default,
    Mako templates are used and so the extension is ``.mako`` but any
    rendered that is recognized by pramid can be used.

    ``template_base_name``: The name of the base template, i.e. from which all
    templates should inherit. Using this you can override the general style
    of the page using a single template instead of having to copy all of
    them and editing them one-by-one. It defaults to ``base``.

    ``button_form``: The form which to use for button actions that should be
    protected by CSRF. Normally, this does not need to be overridden,
    except if a change in those button-only forms such as the delete button
    in the list view is desired. Contrary to a Link this is a necessity to
    prevent CSRF attacks.

    ``delete_form_factory``: A callable which creates a delete form suitable
    for being displayed as a button to delete an item. By default this is
    based on the ``button_form`` attribute and additionally to all
    typical arguments being accepted, it sets the button value to
    ``Delete``.
    """
    __abstract__ = True
    template_dir = 'default'
    template_ext = '.mako'
    template_base_name = 'base'
    button_form = ButtonForm
    delete_form_factory = partial(ButtonForm, title='Delete')

    def __init__(self, request):
        self.request = request
        self._delete_form = None

    def delete_form(self):
        """
        Get the delete form instance, creating a new one if there is none yet.
        This will always return the same instance after multiple calls. This
        shouldn't lead to problems even when the same instance is used for
        multiple elements (like in a list display) since only a button and
        the CSRF hidden field exist on it.
        """
        if self._delete_form is None:
            self._delete_form = self.delete_form_factory(
                self.request.POST, csrf_context=self.request)
        return self._delete_form

    @property
    def dbsession(self):
        return self.request.dbsession

    @property
    def title(self):
        return inspect(self.Form.Meta.model).class_.__name__

    @property
    def title_plural(self):
        return self.title + "s"

    # Misc helper stuff

    @classmethod
    def _template_for(cls, action):
        """
        Return the name of the template to be used. By default this uses the
        template in the folder ``template_dir`` with the name
        ``action + template_ext``, so for example in the default case for a
        list view: "default/list.mako"
        """
        default_name = '%s/%s%s' % (cls.template_dir, action, cls.template_ext)
        return getattr(cls, '%s_template' % action, default_name)

    # Routing stuff

    def redirect(self, route_name=None, *args, **kw):
        """
        Convenience function to create a redirect.

        :param route_name: The name of the route for which to create a URL.
            If this is ``None``, the current route is used.

        All additional arguments and keyword arguments are passed to
        :meth:`pyramid.request.Request.route_url`.

        :return: An instance of :exc:`pyramid.httpexceptions.HTTPFound`
            suitable to be returned from a view to create a redirect.
        """
        if route_name is None:
            route_name = self.request.matched_route.name
        return HTTPFound(
            location=self.request.route_url(route_name, *args, **kw)
        )

    @classmethod
    def route_name(cls, action):
        """
        Get a name for a route of a specific action. The default implementation
        provides the fully quallyfied name of the view plus the action, e.g.
        ``mypackage.views.MyView.list``.
        """
        params = {'module': cls.__module__,
                  'class': cls.__name__,
                  'action': action}
        return "%(module)s.%(class)s.%(action)s" % params

    def _get_route_pks(self, obj):
        """
        Get a dictionary mapping primary key names to values based on the model
        (contrary to :meth:`_get_request_pks` which bases them on the
        request).

        :param obj: An instance of the model.

        :return: A dict with primary key names as keys and their values on the
            object instance as the values.
        """
        Model = self.Form.Meta.model
        pk_names = get_pks(Model)
        kw = {}
        for pk in pk_names:
            kw[pk] = getattr(obj, pk)
            if kw[pk] is None:
                raise ValueError("An obj needs to have all primary keys "
                                 "set or no route can be generated")
        return kw

    def _edit_route(self, obj):
        """
        Get a route for the edit action. Behaves the same as
        :meth:`_delete_route`.
        """
        kw = self._get_route_pks(obj)
        return self.request.route_url(self.route_name('edit'), **kw)

    def _delete_route(self, obj):
        """
        Get a route for the delete action based on the primary keys.

        :param obj: The instance of a model on which the routes values should
            be based.

        :return: A URL which can be used as the routing URL for redirects or
            displaying the URL on the page.
        """
        kw = self._get_route_pks(obj)
        return self.request.route_url(self.route_name('delete'), **kw)

    def _get_request_pks(self):
        """
        Get an ordered dictionary of primary key names matching to their value,
        fetched from the request's matchdict (not the model!).

        :param names: An iterable of names which are to be fetched from the
            matchdict.

        :return: An :class:`.OrderedDict` of the given ``names`` as keys with
            their corresponding value.

        :raises ValueError: When only some primary keys are set (it is allowed
            to have all or none of them set)
        """
        data = OrderedDict((key, self.request.matchdict.get(key, None))
                           for key in get_pks(self.Form.Meta.model))
        nones = [val is None for val in data.values()]
        if any(nones):
            if not all(nones):
                raise ValueError("Either all primary keys have to be set or "
                                 "None")
            else:
                return None
        else:
            return data

    # Actual admin views

    def list(self):
        """
        List all items for a Model. This is the default view that can be
        overridden by subclasses to change its behavior. The attached default
        template is named "default/list.mako".

        :return: A dict with a single key ``items`` that is a query which when
            iterating over yields all items to be listed.
        """
        query = self.dbsession.query(self.Form.Meta.model)
        return {'items': query}

    def delete(self):
        """
        Delete an item. This is the default method for handling deletion and
        can be overridden by subclasses. It only accepts POST request. It has
        no template attached and instead always returns a redirect.

        :return: An instance of :class:`.HTTPFound` to redirect the user,
            either deletion was successful or an error has happened.
        """
        assert self.request.method == 'POST'

        redirect = self.redirect(self.route_name('list'))
        Model = self.Form.Meta.model
        try:
            pks = self._get_request_pks()
            if pks is None:
                raise ValueError("Need primary keys for deletion")
        except ValueError as exc:
            log.info("Invalid Request for primary keys: %s threw exception %s"
                     % (self.request.matchdict, exc))
            self.request.session.flash("Invalid URL", 'error')
            raise redirect

        if not self.delete_form().validate():
            self.request.session.flash("Delete failed.", 'error')
            raise redirect

        obj = self.dbsession.query(Model).get(tuple(pks.values()))
        if obj is not None:
            self.dbsession.delete(obj)
            self.request.session.flash("%s deleted!" % self.title)
            return redirect
        else:
            self.request.session.flash("%s not found!" % self.title, 'error')
            raise redirect

    def edit(self):
        """
        The default view for editing an item. It loads the configured form and
        model. The default template is "default/edit.mako".

        :return: In case of a GET request a dict with the key ``form`` denoting
            the configured form instance with data from an optional model
            loaded and a key ``is_new`` which is a boolean flag indicating
            whether the actual action is ``new`` or ``edit`` (allowing for
            templates to display "New Item" or "Edit Item").

            In case of a POST request, either the same dict is returned or an
            instance of :class:`.HTTPFound` which indicates success in saving
            the item to the database.

        :raises ValueError: In case of an invalid, missing or unmatched action.
            The most likely reason for this is the missing button of a form,
            e.g. by the name ``save``. By default the following actions are
            supported: ``save``, ``save_close``, ``save_new`` and additionally
            anything that starts with ``add_`` or ``delete_`` (these two are
            for internal form handling and inline deletes/adds).
        """
        Model = self.Form.Meta.model

        # determine primary keys
        try:
            pks = self._get_request_pks()
        except ValueError as exc:
            log.info("Invalid Request for primary keys: %s threw exception %s"
                     % (self.request.matchdict, exc))
            self.request.session.flash("Invalid URL", 'error')
            raise self.redirect(self.route_name('list'))

        if pks is not None:
            is_new = False
            obj = self.dbsession.query(Model).get(tuple(pks.values()))
            form = self.Form(self.request.POST, obj, csrf_context=self.request)
        else:
            is_new = True
            form = self.Form(self.request.POST, csrf_context=self.request)
        form.session = self.request.dbsession

        # Prepare return values
        retparams = {'form': form, 'is_new': is_new}

        if self.request.method == 'POST':
            # TODO: Cancel, Save & New, Save & Close, Save
            actions = ['save', 'save_close', 'save_new']
            for action in actions:
                if action in self.request.POST:
                    break
            else:
                for key in self.request.POST:
                    # handled by inline, we are not done editing yet
                    if key.startswith("add_") or key.startswith("delete_"):
                        return retparams
                raise ValueError("Unmatched/Missing Action %s"
                                 % self.request.POST)

            if not form.validate():
                return retparams

            # New object or existing one?
            # Here we do stuff specific to the is_new state, followed by
            # general operations
            if is_new:
                obj = Model()
                self.dbsession.add(obj)
                self.request.session.flash("%s added!" % self.title)
            else:
                self.request.session.flash("%s edited!" % self.title)

            # Transfer edits into database
            form.populate_obj(obj)

            # Determine redirect
            if action == 'save':
                self.dbsession.flush()
                return HTTPFound(location=self._edit_route(obj))
            elif action == 'save_close':
                return self.redirect(self.route_name('list'))
            elif action == 'save_new':
                return self.redirect(self.route_name('new'))
            else:
                # just a saveguard, this is should actually be unreachable
                # because we already check above
                raise ValueError("Unmatched action")  # pragma: no cover
        else:
            return retparams
