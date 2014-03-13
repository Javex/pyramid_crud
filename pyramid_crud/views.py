from pyramid.httpexceptions import HTTPFound
import venusian
from functools import partial
from .util import get_pks
from .forms import ButtonForm
try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict


class CRUDCreator(type):

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
            info = venusian.attach(cls, cb)


class CRUDView(object):
    __metaclass__ = CRUDCreator
    __abstract__ = True
    template_dir = 'default'
    template_ext = '.mako'
    template_base_name = 'base'
    button_form = ButtonForm
    delete_form_factory = partial(ButtonForm, title='Delete')

    def __init__(self, request):
        self.request = request

    @property
    def delete_form(self):
        return self.delete_form_factory(self.request.POST,
                                        csrf_context=self.request)

    @property
    def dbsession(self):
        return self.request.dbsession

    @property
    def title(self):
        return self.form.Meta.model.__mapper__.class_.__name__

    @property
    def title_plural(self):
        return self.title + "s"

    # Misc helper stuff

    @classmethod
    def _template_for(cls, action):
        return '%s/%s%s' % (cls.template_dir, action, cls.template_ext)

    # Routing stuff

    def redirect(self, route_name=None, *args, **kw):
        if route_name is None:
            route_name = self.request.matched_route.name
        return HTTPFound(
            location=self.request.route_url(route_name, *args, **kw)
        )

    @classmethod
    def route_name(cls, type_):
        return '%s_%s' % (cls.__name__.lower(), type_)

    def _get_route_pk(self, obj):
        Model = self.form.Meta.model
        pk_names = get_pks(Model)
        kw = {}
        for pk in pk_names:
            kw[pk] = getattr(obj, pk)
        return kw

    def _edit_route(self, obj):
        kw = self._get_route_pk(obj)
        return self.request.route_url(self.route_name('edit'), **kw)

    def _delete_route(self, obj):
        kw = self._get_route_pk(obj)
        return self.request.route_url(self.route_name('delete'), **kw)

    def _get_pks_from_names(self, names):
        return OrderedDict((key, self.request.matchdict.get(key, None))
                           for key in names)

    # Actual admin views

    def list(self):
        query = self.dbsession.query(self.form.Meta.model)
        return {'items': query}

    def delete(self):
        assert self.request.method == 'POST'

        redirect = self.redirect(self.route_name('list'))
        Model = self.form.Meta.model
        pk_names = get_pks(Model)
        pks = self._get_pks_from_names(pk_names)

        if not self.delete_form.validate():
            self.request.session.flash("Delete failed.")
            return redirect

        obj = self.dbsession.query(Model).get(tuple(pks.values()))
        if obj is not None:
            self.dbsession.delete(obj)
            self.request.session.flash("%s deleted!" % self.title)
        else:
            self.request.session.flash("%s not found!" % self.title)
        return redirect

    def edit(self):
        Model = self.form.Meta.model

        # determine primary keys
        pk_names = get_pks(Model)
        pks = self._get_pks_from_names(pk_names)
        for val in pks.values():
            if val is None:
                is_new = True
                break
        else:
            is_new = False

        if not is_new:
            obj = self.dbsession.query(Model).get(tuple(pks.values()))
            form = self.form(self.request.POST, obj, csrf_context=self.request)
        else:
            form = self.form(self.request.POST, csrf_context=self.request)
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
                    # increase the extra choices by one
                    if key.startswith("add_") or key.startswith("delete_"):
                        return retparams
                raise ValueError("Unmatched/Missing Action")

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
                raise ValueError("Unmatched action")
        return retparams
