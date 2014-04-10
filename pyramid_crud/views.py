from pyramid.httpexceptions import HTTPFound
from pyramid.decorator import reify
from pyramid.renderers import render_to_response
import venusian
import six
import logging
from .util import get_pks
from traceback import format_exc
from .forms import CSRFForm, MultiCheckboxField, SelectField, MultiHiddenField
from wtforms.fields import SubmitField, HiddenField
from wtforms.validators import InputRequired
import sqlalchemy
try:
    from collections import OrderedDict
except ImportError:  # pragma: no cover
    from ordereddict import OrderedDict


log = logging.getLogger(__name__)


class ViewConfigurator(object):
    """
    The standard implementation of the view configuration. It performs the
    most basic configuration of routes and views without any extra
    functionality.

    This is sufficient in many cases, but there are several applications where
    you might want to completely or partially change this behavior. Any time
    you want to pass additional arguments to
    :meth:`pyramid.config.Configurator.add_route` or
    :meth:`pyramid.config.Configurator.add_view` you can just subclass this and
    override the specific methods.

    All the public methods must always be implemented according to their
    documentation or the configuration of views and routes will fail. If you
    are unsure, you can take a look at the default implementation. It is just
    a very thin wrapper around the above mentioned methods.

    During instantiation the arguments ``config`` representing an instance of
    :class:`pyramid.config.Configurator` and ``view_class`` being your
    subclassed view class are given to the instance and stored under these
    values as its attributes.

    From the ``view_class`` parameter you can access the complete configuration
    as documented on :class:`CRUDView`. ``config`` should then be used to add
    routes and views and possibly other configuration you might need.
    """

    def __init__(self, config, view_class):
        self.config = config
        self.view_class = view_class

    def _get_route_name(self, action):
        """
        Get a name for a route of a specific action. The default implementation
        provides the fully quallyfied name of the view plus the action, e.g.
        ``mypackage.views.MyView.list`` (in this case, the action is "list" for
        the class "MyView" in the module "mypackage.views").

        .. note::

            In theory this implementation is ambigous, because you could very
            well have two classes with the same name in the same module.
            However, this would be a very awkward implementation and is not
            recommended anyway. If you really choose to do such a thing, you
            should probably find a better way of naming your routes.
        """
        params = {'module': self.view_class.__module__,
                  'class': self.view_class.__name__,
                  'action': action}
        return "%(module)s.%(class)s.%(action)s" % params

    def _template_for(self, action):
        """
        Return the name of the template to be used. By default this uses the
        template in the folder ``template_dir`` with the name
        ``action + template_ext``, so for example in the default case for a
        list view: "default/list.mako". The parameters ``template_dir`` and
        ``template_ext`` are based on the parameters in :class:`.CRUDView`.
        """
        params = {
            'template_dir': self.view_class.template_dir,
            'action': action,
            'template_ext': self.view_class.template_ext,
        }
        default_name = '%(template_dir)s/%(action)s%(template_ext)s' % params
        return getattr(self.view_class, '%s_template' % action, default_name)

    def _configure_view(self, action, route_action=None, *args, **kw):
        """
        Configure a view via :meth:`pyramid.config.Configurator.add_view` while
        passing any additional arguments to it.

        :param action: The name of the attribute on the view class that
                       represents the action. For example, in the default
                       implementation the ``list`` action corresponds to
                       :meth:`CRUDView.list`. If you rename them, e.g. by
                       naming the ``list`` action "_my_list", this would have
                       to be ``_my_list`` regardless of the name of the
                       action.

        :param route_action: An optional parameter that is used as the name
                             base for the route. If this is missing, it will
                             take the same value as ``action``. In the default
                             implementation it is used to distinguish between
                             ``new`` and ``edit`` which use the same action,
                             view and template but different route names.

        Overriding this method allows you to change the view configuration for
        all configured views at once, i.e. you don't have to change the public
        methods at all. Just look at their default implementation to see the
        parameters they use.
        """
        if route_action is None:
            route_action = action
        self.config.add_view(self.view_class, *args, attr=action,
                             route_name=self._get_route_name(route_action),
                             **kw)

    def _configure_route(self, action, suffix, *args, **kw):
        """
        Set up a route via :meth:`pyramid.config.Configurator.add_route` while
        passing all addtional arguments through to it.

        :param action: The action upon which to base the route name. It must
                       be the same as ``route_action`` on
                       :meth:`._configure_view`.

        :param suffix: The suffix to be used for the actual path. It is
                       appended to the ``url_path`` directly. This may be empty
                       (as is the case for the default list view) but must
                       always be explicitly specified. The result of this will
                       be passed to ``add_route`` and so may (and often will)
                       include parameters such as ``/{id}``.

        Overriding this method can be done in the same manner as described for
        :meth:`._configure_view`.

        .. warning::

            Some methods on the view require primary keys of the object in
            question in the ``matchdict`` of the request. To guarantee this,
            the routes have to be correctly set up, i.e. each route that
            requires this primary key (or keys, depending on the model) has to
            have a pattern where each primary key name appears once. The
            default implementation takes care of this via
            :meth:`_get_route_pks`, but if you change things you have to
            ensure this yourself.

            Which methods require which values is documented on the respective
            views of :class:`CRUDView`.
        """
        # suffix may be something like /new or /{id} etc. May also be empty,
        # e.g. for the list view.
        params = {
            'base_path': self.view_class.url_path,
            'suffix': suffix
        }
        url = '%(base_path)s%(suffix)s' % params
        route_name = self._get_route_name(action)
        self.config.add_route(route_name, url, *args, **kw)
        return route_name

    def _get_route_pks(self):
        """
        Get a string representing all primary keys for a route suitable to
        be given as suffix to :meth:`._configure_route`. Some examples will
        probably best describe the default behavior.

        In the case of a model with a single primary key ``id``, the result is
        the very simple string ``{id}``. If you add this to a route, the
        primary key of the object will be in the ``matchdict`` under the key
        ``id``.

        If you have a model with multiple primary keys, say composite foreign
        keys, called ``model1_id`` and ``model2_id`` then the result would be
        ``{model1_id},{model2_id}``. The order is not important on this one as
        pyramids routing system will fully take care of it.

        .. note::

            If you have some kind of setup where one of the primary keys may
            contain a comma, this implementation is likely to fail and you
            have to change it. However, in most cases you will **not** have a
            comma and this should be fine.
        """
        model = self.view_class.Form.Meta.model
        pks = ",".join('{%s}' % pk_name for pk_name in get_pks(model))
        return pks

    def configure_list_view(self):
        """
        Configure the "list" view by setting its route and view. This method
        must call ``add_view`` to configure the view and ``add_route`` to
        connect a route to it. Afterwards, it must return the name of the
        configured route that links route and view. This will then be
        stored in the view's ``route`` dictionary under the "list" key.

        .. code-block:: python

            def configure_list_view(self):
                self.config.add_view('myview-list',
                                     renderer='default/list.mako',)
                self.config.add_route('myview-list', self.view_class.url_path)
                return 'myview-list'

        This does a few things:

        * It sets up the view under the alias ``myview-list`` with the template
          ``default/list.mako`` (the standard list template).

        * It connects the alias to the configured route via the
          :ref:`url_path <url_path>` configuration parameter (the list view is
          just the base route in this case, but that is totally up to you).

        * It returns this alias from the function so that it can be stored in
          the ``routes`` dictionary on the view.
        """
        self._configure_view('list', renderer=self._template_for('list'))
        return self._configure_route('list', '')

    def configure_edit_view(self):
        """
        This method behaves exactly like
        :meth:`ViewConfigurator.configure_list_view` except it must configure
        the edit view, i.e. the view for editing existing objects. It must
        return the name of the route as well that will then be stored under the
        "edit" key.
        """
        self._configure_view('edit', renderer=self._template_for('edit'))
        return self._configure_route('edit',
                                     '/%s/edit' % self._get_route_pks())

    def configure_new_view(self):
        """
        This method behaves exactly like
        :meth:`ViewConfigurator.configure_list_view` except it must configure
        the new view, i.e. the view for adding new objects. It must
        return the name of the route as well that will then be stored under the
        "new" key.
        """
        self._configure_view('edit', 'new',
                             renderer=self._template_for('edit'))
        return self._configure_route('new', '/new')


class CRUDCreator(type):
    """
    Metaclass for :class:`CRUDView` to handle automatically registering views
    for new subclasses.
    """

    def __init__(cls, name, bases, attrs):
        def cb(context, name, ob):
            config = context.config.with_package(info.module)
            configurator = cls.view_configurator(config, cls)
            list_route = configurator.configure_list_view()
            edit_route = configurator.configure_edit_view()
            new_route = configurator.configure_new_view()

            cls.routes = {
                'list': list_route,
                'edit': edit_route,
                'new': new_route,
            }
        if '__abstract__' not in attrs:
            have_attrs = set(attrs)
            need_attrs = set(('Form', 'url_path'))
            if have_attrs & need_attrs != need_attrs:
                missing = need_attrs - (have_attrs & need_attrs)
                raise AttributeError(
                    "Invalid configuration. The following attributes are "
                    "missing and need to be defined for a complete "
                    "configuration : %s" % ", ".join(missing))
            if cls.view_configurator is not None:
                info = venusian.attach(cls, cb)

            # Initialize mutable defaults
            cls.actions = []


@six.add_metaclass(CRUDCreator)
class CRUDView(object):
    """
    The base class for all views. Subclassing directly from this gets you a
    new view configuration for a single model & form. If you specify
    ``__abstract__`` on it, the class will not be configured at all and you can
    use it as your own base class.

    .. note::

        Configuration is done by Pyramid the moment you call
        :meth:`pyramid.config.Configurator.scan` in a way similar to what
        the :class:`pyramid.view.view_config` decorator does. If you want to
        completely disable this behavior, set
        :ref:`view_configurator <view_configurator_cfg>` to ``None``. Then no
        route configuration will be done and you have to set up views and
        routes yourself. This is an advanced technique not recommended for
        beginners.

    The following attributes can be defined to override behavior of the view:

    .. _crud_Form:

    Form
        Mandatory argument that specifies the form class for which this
        view should be created. This must be a form as described in
        :ref:`forms`.

    .. _url_path:

    url_path
        Mandatory arguments if the default
        :ref:`view_configurator <view_configurator_cfg>` is used. It determines
        the base path under which this view should be available.

        So for example, if this is ``/myitems`` then the list view will be
        reached under the ``/myitems`` path whereas the new view will be
        under ``/myitems/new``.

        How and if this parameter is used depends entirely on the
        implementation of the configurator but it is recommended to keep this
        parameter for custom implementations as well.

    dbsession
        Return the current SQLAlchemy session. By default this
        expects a ``dbsession`` attribute on the ``request`` object. It is
        **mandatory** that you either attach the attribute using an event
        or override this attribute (you can use a :class:`property` if you
        like).

    .. _list_display:

    list_display
        A tuple if items which should be displayed on the list
        view. By default a single column of the models ``__str__`` method is
        used. There are several possibilities of what you might specify here
        (the options will be tried in this order):

        * A string representing an attribute or callable on the model. If this
          attribute is callable, it will be called and get no additional
          arguments (the first argument will already be ``self``, the model
          instance).

          For example, with a normal field on the model:

          .. testcode::

             class Model(Base):
                  id = Column(Integer, primary_key=True,
                              info={'label': 'ID'})

             class View(CRUDView):
                  list_display = ('id',)

          In this example there will be a single column in the list view. Its
          title will be "ID" and its value will be the value of the ``id``
          field in the database.

          Similarly, with a callable:

          .. testcode::

              class Model(Base):
                  id = Column(Integer, primary_key=True)

                  def id_plus_one(self):
                      return self.id + 1
                  id_plus_one.info = {'label': 'ID+1'}

              class View(CRUDView):
                  list_display = ('id_plus_one',)

        * A generic callable function. This function will be called with a
          single argument: The instance of the model. For example:

          .. testcode::

              class Model(Base):
                  id = Column(Integer, primary_key=True)

              def id_plus_one(obj):
                  return obj.id + 1
              id_plus_one.info  = {'label': 'ID+1'}

              class View(CRUDView):
                  list_display = (id_plus_one,)

        * A string representing a method on the view. This will behave in the
          same way as for the function callable above except that it must be
          a string. For example:

          .. testcode::

              class Model(Base):
                  id = Column(Integer, primary_key=True)

              class View(CRUDView):
                  list_display = ('id_plus_one',)

                  def id_plus_one(self, obj):
                      return obj.id + 1
                  id_plus_one.info = {'label': 'ID+1'}

        Some additional notes on the way this attribute behaves:

        * Some additional configuration is possible on each attribute,
          regardless of how it is specified. For information on this see
          :ref:`info_dict`.

        * A class ``columnn-<attr-name>`` is placed on each on each of the
          <th> fields in the column heading to allow application of CSS
          attributes, e.g. to set the width of a column.

        * If the attribute ``info`` cannot be found on the attribute (at the
          class level, not instance level), default value is determined as the
          column heading. If name of the column is ``__str__`` then the name
          of the model class is fetched. If it is directly callable (in case
          of a generic callable function), then the name of the function is
          used. In all other cases the provided string is used. To make for
          a prettier format, it additionally replaces any underscores by
          spaces and captializes each word.

    .. _list_display_links:

    list_display_links
        Specify which of the displayed columns should be turned into links
        that open the edit view of that instance. By default, the first
        column is used.

        This should be any kind of iterable, preferrably a tuple or set for
        performance reasons.

        Example:

        .. code-block:: python

            class MyView(CRUDView):
                list_display = ('column1', 'column2', 'column3')
                list_display_links = ('column1', 'column3')

        This configuration will turn the columns ``column1`` and ``column3``
        into links.

    .. _actions_cfg:

    actions:
        An optional list of action callables or view method names for the
        dropdown menu. See :ref:`actions` for details on how to use it.

    template_dir
        The directory where to find templates. The default
        templates are provided in the ``default`` folder. This is used
        by the default :ref:`view_configurator <view_configurator_cfg>` and not
        necessarily used if you change its behavior.

    template_ext
        Which file extension to use for templates. By default,
        Mako templates are used and so the extension is ``.mako`` but any
        rendered that is recognized by pramid can be used. This is used
        by the default :ref:`view_configurator <view_configurator_cfg>` and not
        necessarily used if you change its behavior.

    template_base_name
        The name of the base template, i.e. from which all
        templates should inherit. Using this you can override the general style
        of the page using a single template instead of having to copy all of
        them and editing them one-by-one. It defaults to ``base``.

        .. todo::

            Implement / Test / Document better

    .. _view_configurator_cfg:

    view_configurator
        A class that configures all views and routes for this view class. The
        default implementation is :class:`ViewConfigurator` which covers
        basic route & view configuration. However, if you need more advanced
        functionalities like, for example, permissions, you can change this
        parameter. See the documentation on :class:`ViewConfigurator` for
        details on how to achieve that.

    There are also some attributes which you can access. All of them are
    available on the instance, but only some are also available on the class
    (in this case, it is noted on the attribute).

    routes
        A dictionary mapping action names to routes. Action names are such as
        ``list`` or ``edit`` and they all have unique route names that can be
        given to ``request.route_url``. You can use it like this:

        .. code-block:: python

            url = request.route_url(view.routes["list"])

        This will return a URL to the list view.

        The routes dictionary is populated by the
        :ref:`view_configurator <view_configurator_cfg>`.

        This can be accessed at the class and instance level.

    request
        The current request, an instance of :class:`pyramid.request.Request`.
    """
    __abstract__ = True
    template_dir = 'default'
    template_ext = '.mako'
    template_base_name = 'base'
    view_configurator = ViewConfigurator

    def __init__(self, request):
        self.request = request
        self._action_form = None

    def _get_item_choices(self):
        pks = get_pks(self.Form.Meta.model)
        if len(pks) != 1:
            raise ValueError("Can only handle a single primary key")
        [pk] = pks

        cb_choices = []
        for item in self.get_list_query():
            cb_choices.append((str(getattr(item, pk)), ''))
        return cb_choices

    def get_action_form(self):
        if self._action_form is None:
            action_choices = [('', '--- Select Action ---')]
            action_choices += [(name, info['label'])
                               for name, info in self._all_actions.items()]

            req_validator = InputRequired('You must select at least one '
                                          'item')
            cb_choices = self._get_item_choices()

            class ActionForm(CSRFForm):
                action = SelectField('Action:', choices=action_choices)
                items = MultiCheckboxField(choices=cb_choices,
                                           validators=[req_validator])
                submit = SubmitField("Execute")

            self._action_form = ActionForm
        return self._action_form

    @property
    def dbsession(self):
        return self.request.dbsession

    @property
    def list_display(self):
        return ('__str__',)

    @reify
    def _all_actions(self):
        """
        Get a list of all actions, including default ones.
        """
        all_actions = OrderedDict()
        for action in [self.delete] + self.actions:
            if not callable(action):
                action = getattr(self, action)
            info = dict(getattr(action, "info", {}))
            info["func"] = action
            if "label" not in info:
                info["label"] = action.__name__.replace("_", " ").title()
            all_actions[action.__name__] = info
        return all_actions

    def delete(self, query):
        """
        Delete all objects in the ``query``.
        """
        try:
            req_validator = InputRequired('You must select at least one '
                                          'item')

            class ConfirmationForm(CSRFForm):
                action = HiddenField()
                confirm_delete = SubmitField('Delete')
                items = MultiHiddenField(choices=self._get_item_choices(),
                                         validators=[req_validator])
            form = ConfirmationForm(self.request.POST,
                                    csrf_context=self.request)
            items = query.all()
            if 'confirm_delete' in self.request.POST:
                if not form.validate():
                    # Likely CSRF or other fiddling, don't bother checking
                    raise Exception

                item_count = len(items)
                for item in items:
                    self.dbsession.delete(item)
                self.dbsession.flush()
                if item_count == 1:
                    title = self.Form.title
                else:
                    title = self.Form.title_plural
                message = "%d %s deleted!" % (item_count, title)
                self.request.session.flash(message)
                return True, None
            else:
                data = {'items': items, 'view': self, 'form': form}
                response = render_to_response('default/delete_confirm.mako',
                                              data, request=self.request)
                return True, response
        except Exception:
            log.warning("Deletion of items failed:\n%s" % format_exc())
            self.request.session.flash('There was an error deleting the '
                                       'item(s)', 'error')
            return False, None
    delete.info = {'label': 'Delete'}

    # Misc helper stuff

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
        Get a route for the edit action based on an objects primary keys.

        :param obj: The instance of a model on which the routes values should
            be based.

        :return: A URL which can be used as the routing URL for redirects or
            displaying the URL on the page.
        """
        kw = self._get_route_pks(obj)
        return self.request.route_url(self.routes['edit'], **kw)

    # Template helper functions

    def iter_head_cols(self):
        """
        Get an iterable of column headings based on the configuration in
        ``list_display``.
        """
        for col in self.list_display:
            col_name = col
            if callable(col_name):
                col_name = col_name.__name__
            model = self.Form.Meta.model
            if isinstance(col, (six.text_type, six.binary_type)):
                if hasattr(model, col):
                    col = getattr(model, col)
                elif hasattr(self, col):
                    col = getattr(self, col)
                else:
                    raise AttributeError("No attribute of name '%s' on model "
                                         "or view found")
            # Create a copy
            if hasattr(col, 'info'):
                col_info = dict(col.info)
            else:
                if col_name == '__str__':
                    label = model.__name__
                    col_name = label
                else:
                    label = col_name
                label = label.replace("_", " ").title()
                col_info = {'label': label}
            if (hasattr(col, 'type') and
                    isinstance(col.type, sqlalchemy.Boolean)):
                col_info["bool"] = True
            col_info.setdefault("css_class", "column-%s" % col_name)
            yield col_info

    def iter_list_cols(self, obj):
        """
        Get an iterable of columns for a given obj suitable as the columns for
        a single row in the list view. It uses the ``list_display`` option to
        determine the columns.
        """
        for col in self.list_display:
            title = col
            if callable(title):
                title = title.__name__
            if isinstance(col, (six.text_type, six.binary_type)):
                if hasattr(obj, col):
                    col = getattr(obj, col)
                    if callable(col):
                        col = col()
                # column on view
                else:
                    col = getattr(self, col)
                    if callable(col):
                        col = col(obj)
            # must be a separate callable
            else:
                col = col(obj)
            yield title, col

    def get_list_query(self):
        return self.dbsession.query(self.Form.Meta.model)

    # Actual admin views

    def list(self):
        """
        List all items for a Model. This is the default view that can be
        overridden by subclasses to change its behavior. The attached default
        template is named "default/list.mako".

        :return: A dict with a single key ``items`` that is a query which when
            iterating over yields all items to be listed.
        """
        ActionForm = self.get_action_form()
        action_form = ActionForm(self.request.POST, csrf_context=self.request)
        items = self.get_list_query()
        retparams = {'items': items, 'action_form': action_form}

        if self.request.method == 'POST':
            redirect = self.redirect(self.routes['list'])
            Model = self.Form.Meta.model
            pk_names = get_pks(Model)
            if len(pk_names) != 1:  # pragma: no cover (covered above already)
                raise ValueError("Only single primary keys supported right "
                                 "now")
            pk = getattr(Model, pk_names[0])
            value_list = action_form.items.data
            if not action_form.validate():
                flash = self.request.session.flash
                if 'csrf_token' not in action_form.errors:
                    if 'items' in action_form.errors:
                        for msg in action_form.errors['items']:
                            flash(msg, 'error')

                    if 'action' in action_form.errors:
                        for msg in action_form.errors['action']:
                            flash(msg, 'error')
                return retparams

            action = self._all_actions[action_form.action.data]
            query = self.dbsession.query(Model).filter(pk.in_(value_list))
            success, response = action["func"](query)
            if success:
                return response or redirect
            else:
                raise response or redirect
        return retparams

    def edit(self):
        """
        The default view for editing an item. It loads the configured form and
        model. The default template is "default/edit.mako". In edit mode (i.e.
        with an already existing object) it requires
        a matchdict mapping primary key names to their values. This has to be
        ensured during route configuring by setting the correct pattern. The
        default implementation takes correctly care of this.

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
            raise self.redirect(self.routes['list'])

        if pks is not None:
            is_new = False
            obj = self.dbsession.query(Model).get(tuple(pks.values()))
            form = self.Form(self.request.POST, obj, csrf_context=self.request)
        else:
            is_new = True
            form = self.Form(self.request.POST, csrf_context=self.request)
        form.session = self.dbsession

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
                self.request.session.flash("%s added!" % self.Form.title)
            else:
                self.request.session.flash("%s edited!" % self.Form.title)

            # Transfer edits into database
            form.populate_obj(obj)

            # Determine redirect
            if action == 'save':
                self.dbsession.flush()
                return HTTPFound(location=self._edit_route(obj))
            elif action == 'save_close':
                return self.redirect(self.routes['list'])
            elif action == 'save_new':
                return self.redirect(self.routes['new'])
            else:
                # just a saveguard, this is should actually be unreachable
                # because we already check above
                raise ValueError("Unmatched action")  # pragma: no cover
        else:
            return retparams
