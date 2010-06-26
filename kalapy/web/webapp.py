# -*- coding: utf-8 -*-
"""
kalapy.web
~~~~~~~~~~

This module implements web component API on top of `Werkzeug`. It also provides
template support using Jinja2 and exposes some useful api from `werkzeug` and
`jinja2` packages.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LICENSE for more details.
"""
import os, sys

try:
    import simplejson as json
except ImportError:
    import json

from jinja2 import Environment, BaseLoader, FileSystemLoader
from werkzeug import Request as BaseRequest, Response as BaseResponse, \
        ClosingIterator, SharedDataMiddleware, import_string, redirect
from werkzeug.exceptions import HTTPException
from werkzeug.local import Local, LocalManager
from werkzeug.routing import Rule, Map

from kalapy.conf import settings
from kalapy.utils import signals


__all__ = (
    'request',
    'route',
    'url_for',
    'locate',
    'jsonify',
    'render_template',
    'simple_server',
    'Request',
    'Response',
    'Package',
    'Application',
    'Middleware'
)


# context local support
_local = Local()
_local_manager = LocalManager([_local])

# context local variable
request = _local('request')


class Request(BaseRequest):
    """The request object, remembers the matched endpoint, view arguments and
    current package.
    """

    @property
    def package(self):
        if self.endpoint:
            return self.endpoint.split('.', 1)[0]


class Response(BaseResponse):
    """The response object that is used by default, with default mimetype
    set to `'text/html'`.
    """
    default_mimetype = 'text/html'


class PackageType(type):
    """A meta class to ensure only one instance of :class:`Package` exists
    for a given package name.
    """

    #: cache of all the Package instances
    ALL = {}

    def __call__(cls, *args):
        name = args[0] if args else None
        if name not in cls.ALL:
            cls.ALL[name] = super(PackageType, cls).__call__(*args)
        return cls.ALL[name]

    def from_view(cls, view_func):
        """A factory method to create package instance from the view function.
        """
        module = view_func.__module__
        name = module[:module.find('.views')].rsplit('.', 1)[-1]
        return cls(name)


class Package(object):
    """Container object that represents an installed package.

    A package can be enabled/disabled from `settings.INSTALLED_PACKAGES`. This
    class is intended for internal use only.

    For more information on packages, see...

    :param name: name of the package
    :param path: directory path where package is located
    """
    __metaclass__ = PackageType

    #: :class:`werkzeug.routing.Map` instance, shared among all the Packages
    urls = Map()

    #: view functions, shared among all the packages
    views = {}

    def __init__(self, name, path=None):

        if path is None:
            path = os.path.abspath(os.path.dirname(sys.modules[name].__file__))

        self.name = name
        self.path = path

        opts = settings.PACKAGE_OPTIONS.get(name, {})
        self.submount = opts.get('submount')

        # static dir info
        self.static = os.path.join(self.path, 'static')
        if not os.path.isdir(self.static):
            self.static = None

        # add rule for static urls
        if self.static:
            prefix = '/static' if self.is_main else '/%s/static' % name
            self.add_rule('%s/<filename>' % prefix, 'static', build_only=True)
            prefix = '%s%s' % (self.submount or '', prefix)
            self.static = (prefix, self.static)

        # create template loader
        self.jinja_loader = FileSystemLoader(self.get_resource_path('templates'))

    @property
    def is_main(self):
        """Whether this is the main package (the project package)
        """
        return self.name == settings.PROJECT_NAME

    def get_resource_path(self, name):
        """Get the absolute path the the given resource.

        :param name: path to the resource relative to this package
        """
        return os.path.join(self.path, name)

    def get_resource_stream(self, name):
        """Returns file stream object of the given resource.

        :param name: path to the resource relative to this package
        """
        return open(self.get_resource_path(name), 'rb')

    def add_rule(self, rule, endpoint, func=None, **options):
        """Add URL rule with the specified rule string, endpoint, view
        function and options.

        Function must be provided if endpoint is None. In that case endpoint
        will be automatically generated from the function name. Also, the
        endpoint will be prefixed with current package name.

        Other options are similar to :class:`werkzeug.routing.Rule` constructor.
        """
        if endpoint is None:
            assert func is not None, 'expected view function if endpoint' \
                    ' is not provided'

        if endpoint is None:
            endpoint = '%s.%s' % (func.__module__, func.__name__)
            __, endpoint = endpoint.rsplit('views.', 1)

        if not self.is_main:
            endpoint = '%s.%s' % (self.name, endpoint)

        options.setdefault('methods', ('GET',))
        options['endpoint'] = endpoint

        if self.submount:
            rule = '%s%s' % (self.submount, rule)

        self.urls.add(Rule(rule, **options))
        self.views[endpoint] = func

    def route(self, rule, **options):
        """Same as :func:`route`
        """
        def wrapper(func):
            self.add_rule(rule, None, func, **options)
            return func
        return wrapper


class Middleware(object):
    """Application middleware objects (don't confuse with WSGI middleware).
    This is more similar to `Django's` middleware. It allows to hook into
    application's request/response cycle. It's a ligh, low-level 'plugin'
    system for globally alter the the application input/output.

    It defines following interface methods, which derived middleware classes
    should override.

    `process_request`

        this method will be called before request starts.

    `process_response`

        this method will be called after request is finished and response
        is successfully generated.

    `process_exception`

        this method will be called when any exception occurred during request/
        response cycle.

    For more information on middleware, see...
    """

    def process_request(self, request):
        """This method will be called before request starts.
        """
        pass

    def process_response(self, request, response):
        """This method will be called after response is successfully generated.
        """
        pass

    def process_exception(self, request, exception):
        """This method will be called if any exception occurs during request/
        response cycle.
        """
        pass


class Application(Package):
    """The Application class implements a WSGI application. This class is
    responsible to request dispatching, middleware processing, generating
    proper response from the view function return values etc.
    """

    def __init__(self):

        # load all the settings.INSTALLED_PACKAGES
        from kalapy.conf.loader import loader
        loader.load()

        super(Application, self).__init__(
                settings.PROJECT_NAME,
                settings.PROJECT_DIR)

        self.debug = settings.DEBUG
        _local.current_app = self

        #: list of all the registered middlewares
        self.middlewares = []

        # register all the settings.MIDDLEWARE_CLASSES
        for mc in settings.MIDDLEWARE_CLASSES:
            mc = import_string(mc)
            self.middlewares.append(mc())

        # static data middleware
        static_dirs = [p.static for p in Package.ALL.values() if p.static]
        if self.static:
            static_dirs.append(self.static)
        self.dispatch = SharedDataMiddleware(self.dispatch, dict(static_dirs))

    def process_request(self, request):
        """This method will be called before actual request dispatching and
        will call all the registered middleware's respective `process_request`
        methods. If any of these methods returns any values, it is considered
        as if it was the return value of the view function and further request
        handling will be stopped.
        """
        for mw in self.middlewares:
            rv = mw.process_request(request)
            if rv is not None:
                return rv

    def process_response(self, request, response):
        """This method will be called after response is successfully created and
        will call all the registered middleware's respective `process_response`
        methods.
        """
        for mw in reversed(self.middlewares):
            rv = mw.process_response(request, response)
            if rv is not None:
                return rv
        return response

    def process_exception(self, request, exception):
        """This method will be called if there is any unhandled exception
        occurs during request handling. In turn, this method will call all the
        registered middleware's respective `process_exception` methods.
        """
        for mw in self.middlewares:
            rv = mw.process_exception(request, exception)
            if rv is not None:
                return rv

    def make_response(self, value):
        """Converts the given value into a real response object that is an
        instance of :class:`Response`.

        :param value: the value to be converted
        """
        if value is None:
            raise ValueError('View function should return a response')
        if isinstance(value, Response):
            return value
        if isinstance(value, basestring):
            return Response(value)
        if isinstance(value, tuple):
            return Response(*value)
        return Response.force_type(value, request.environ)

    def get_response(self, request):
        """Returns an :class:`Response` instance for the given `request` object.
        """
        response = self.process_request(request)
        if response is not None:
            return response
        endpoint, args = request.url_adapter.match()

        request.endpoint = endpoint
        request.view_args = args
        request.view_func = func = self.views[endpoint]

        try:
            return self.make_response(func(**args))
        except Exception, e:
            response = self.process_exception(request, e)
            if response is not None:
                return response
            raise

    def dispatch(self, environ, start_response):
        """The actual wsgi application. This is not implemented in `__call__`
        so that wsgi middlewares can be applied without losing a reference to
        the class.
        """
        _local.current_app = self
        _local.request = request = Request(environ)
        request.url_adapter = adapter = self.urls.bind_to_environ(environ)

        signals.send('request-started')
        try:
            response = self.get_response(request)
        except HTTPException, e:
            response = e
        except Exception, e:
            signals.send('request-exception', error=e)
            raise
        finally:
            signals.send('request-finished')

        response = self.process_response(request, response)

        return ClosingIterator(response(environ, start_response),
                [_local_manager.cleanup])

    def __call__(self, environ, start_response):
        return self.dispatch(environ, start_response)


def route(rule, **options):
    """A decorator to register a view function for a given URL rule.

    Example::

        @web.route('/<path:page>')
        def index(page):
            ...

        @web.route('/<path:page>', methods=('POST',))
        def save(page):
            ...

        @web.route('/<path:page>/edit')
        def edit(page):
            ...

    For more information, see...

    :param rule: the URL rule as string
    :param methods: a list of http methods this rule is limited to like
                   (``'GET'``, ``'POST'``, etc). By default a rule is
                   limited to ``'GET'`` (and implicitly ``'HEAD'``).
    :param options: other options to be forwarded to the underlying
                    :class:`werkzeug.routing.Rule` object.
    """
    def wrapper(func):
        package = Package.from_view(func)
        return package.route(rule, **options)(func)
    return wrapper


def url_for(endpoint, **values):
    """Generate a URL for the given endpoint with the method provided. The
    endpoint is relative to current package. If you wish to refers an endpoint
    from another package prefix it like `package:endpoint` and `module.endpoint`
    to refer from another module in the same package and `.endpoint` to refer
    to the function in the same module.

    Here are few examples:

    =============== =================== ==============================
    Active Package  Target Endpoint     Target Function
    =============== =================== ==============================
    `blog`          ``'index'``         `blog.views.index`
    `blog`          ``'page.index'``    `blog.views.page.index`
    `blog`          ``'.edit'``         `blog.views.page.edit`
    `wiki`          ``'index'``         `wiki.views.index`
    `blog`          ``'wiki:index'``    `wiki.views.index`
    `any`           ``'wiki:index'``    `wiki.views.index`
    `any`           ``'blog:index'``    `blog.views.index`
    =============== =================== ==============================

    Where `blog.views.index` is defined in `blogs/views/__init__.py` and
    `blog.views.page.index` is defined in `blogs/views/page.py` and so on.

    Variable arguments that are unknown to the target endpoint are appended
    to the generated URL as query arguments.

    This function can also be used to generate URL for static contents in
    templates. In that case, if you want to refer global static dir then
    just prefix the endpoint with ':' like `:static`.

    Here are few examples:

    =============== =================== ==============================
    Active Package  Target Endpoint     Target Static Dir
    =============== =================== ==============================
    `blog`          ``'static'``        `/blog/static`
    `wiki`          ``'static'``        `/wiki/static`
    `any`           ``':static'``       `/static`
    `any`           ``'blog:static'``   `/blog/static`
    =============== =================== ==============================

    For more information, see...

    :param endpoint: the endpoint for the URL
    :param values: the variable arguments for the URL
    :param _external: if set to True, an absolute URL will be generated.

    :returns: generate URL string
    :raises: :class:`BuildError`
    """

    reference = None
    external = values.pop('_external', False)

    if ':' in endpoint:
        reference, endpoint = endpoint.split(':', 1)

    if endpoint == 'static':
        if reference is None:
            reference = request.package
    else:
        if endpoint.startswith('.'):
            endpoint = endpoint[1:]
            reference = request.endpoint.rsplit('.', 1)[0]
        if not reference:
            reference = request.package
    if reference:
            endpoint = '%s.%s' % (reference, endpoint)
    return request.url_adapter.build(endpoint, values, force_external=external)


def locate(endpoint, **values):
    """Similar to `werkzeug.redirect` but uses `url_for` to generate
    target location from the url rules.

    :param endpoint: the endpoint for the URL
    :param values: the variable arguments for the URL
    :param _external: if set to True, an absolute URL will be generated.
    :param _code: http status code, default 302
    """
    code = values.pop('_code', 302)
    return redirect(url_for(endpoint, **values), code)


class JinjaLoader(BaseLoader):
    """Custom Jinja template loader, loads the template from the
    current package.
    """
    def get_source(self, environment, template):
        package, name = template.split(':', 1)
        try:
            package = Package.ALL[package or None]
            template = name
        except KeyError:
            package = Package.ALL[None]
        return package.jinja_loader.get_source(environment, template)


class JinjaEnvironment(Environment):
    """Custom Jinja environment, makes sure that template is correctly resolved.
    """
    def join_path(self, template, parent):
        if ':' not in template:
            package = parent.split(':',1)[0]
            return '%s:%s' % (package, template)
        return template


jinja_env = JinjaEnvironment(
    loader=JinjaLoader(),
    autoescape=True,
    extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_'])


jinja_env.globals.update(
        url_for=url_for,
        request=request)

if settings.USE_I18N:
    from kalapy.i18n.utils import gettext, ngettext
    jinja_env.add_extension('jinja2.ext.i18n')
    jinja_env.install_gettext_callables(gettext, ngettext, newstyle=True)


def render_template(template, **context):
    """Render the template from the `templates` folder of the current package
    with the given context.

    If you want to refer to a template from another package, prefix the name
    with that package name like `package:template`. Also, if you wish to refer
    to a template from the global template dir just prefix it with `:`.

    Here are few examples:

    =============== ===================== ==============================
    Active Package  Template Name         Terget Template
    =============== ===================== ==============================
    `blog`          ``'index.html'``      '/blog/templates/index.html'
    `wiki`          ``'index.html'``      '/wiki/templates/index.html'
    `any`           ``'blog:index.html``  '/blog/templates/index.html'
    `any`           ``':index.html``      '/templates/index.html'
    =============== ===================== ==============================

    Same rule applies to the `extends` and `inculde` templates directives.

    .. note::

        If you refer a template from another package, all the `extends`,
        `include` and `import` statements will be resolved with current
        package's template loader if the template names are not prefixed
        appropriately. Same is true for `url_for` used within the referenced
        template

    :param template: the name of the template to be rendered.
    :param context: the variables that should be available in the context
                    of the template.

    :returns: string generated after rendering the template
    :raises: :class:`TemplateNotFound` or any other exceptions thrown during
             rendering process
    """
    if ':' not in template:
        template = '%s:%s' % (request.package, template)
    return jinja_env.get_template(template).render(context)


def jsonify(*args, **kw):
    """Creates a :class:`Response` with JSON representation of the given
    data provided from the arguments with an `application/json` mimetype.
    The arguments to this function are same as :class:`dict` constructor.

    Example::

        @web.route('/user/info')
        def get_user():
            return jsonify(name="somename", active=True, key=34)

    This will send a JSON response to the client like this::

        {
            'name': 'somename',
            'active': true,
            'key': 34
        }

    :returns: an instance of :class:`Response`
    """
    return Response(json.dumps(dict(*args, **kw)), mimetype='application/json')


def simple_server(host='127.0.0.1', port=8080, use_reloader=False):
    """Run a simple server for development purpose.

    :param host: host name
    :param post: port number
    :param use_reloader: whether to reload the server if any of the loaded
                         module changed.
    """
    from werkzeug import run_simple
    # create a wsgi application
    app = Application()
    app.debug = debug = settings.DEBUG
    run_simple(host, port, app, use_reloader=use_reloader, use_debugger=debug)

