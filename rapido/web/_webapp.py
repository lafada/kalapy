# -*- coding: utf-8 -*-
"""
    rapido.web
    ~~~~~~~~~~

    This module implements web component API on top of `werkzeug`. The API is
    highly inspired of the `Flask`, a microframework. 
    
    :copyright: (c) 2010 Amit Mendapara.
    :license: BSD, see LICENSE for more details.
"""
import re, os, sys, types

try:
    import json
except ImportError:
    import simplejson as json

from werkzeug import (
    Request as BaseRequest,
    Response as BaseResponse,
    ClosingIterator,
    SharedDataMiddleware,
    Href, redirect,
)

from werkzeug.routing import Rule, Map, Submount
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError
from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.local import Local, LocalManager

from jinja2 import Environment, FunctionLoader, Markup, escape

from rapido.conf import settings


# context local support
_local = Local()
_local_manager = LocalManager([_local])

# context local variable
request = _local('request')
session = _local('session')


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


class Session(SecureCookie):
    """Implemented session object with :class:`SecureCookie`.
    """
    pass


class PackageType(type):
    """A meta class to ensure only one instance of :class:`Package` exists
    for a given package name.
    """

    #: cache of all the Package instances
    ALL = {}

    def __call__(cls, name):
        if name not in cls.ALL:
            cls.ALL[name] = super(PackageType, cls).__call__(name)
        return cls.ALL[name]

    def from_view(cls, view_func):
        """A factory method to create package instance from the view function.
        """
        module = view_func.__module__
        name = module[:module.find('.views')].rsplit('.', 1)[-1]
        return cls(name)


class Package(object):
    """Container object that reprensents an installed package.
    
    A package can be enabled/disabled from `settings.INSTALLED_PACKAGES`. This
    class is intended for internal use only.
    
    For more information on packages, see...

    :param name: name of the package
    """
    __metaclass__ = PackageType

    def __init__(self, name):
        self.name = name
        self.path = os.path.abspath(os.path.dirname(sys.modules[name].__file__))
        self.rules = [(Rule('/%s/static/<filename>' % name, 
            endpoint='%s.static' % name, build_only=True), None)]

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

    def route(self, rule, **options):
        """Same as :func:`route`
        """
        def wrapper(func):
            endpoint = '%s.%s' % (func.__module__, func.__name__)
            endpoint = endpoint[-endpoint.rfind('views.')+1:]
            endpoint = '%s.%s' % (self.name, endpoint)
            options.setdefault('methods', ('GET',))
            options['endpoint'] = endpoint
            self.rules.append((Rule(rule, **options), func))
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

        this method will be called when any exception occured during request/
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


class StaticMiddleware(SharedDataMiddleware):

    def __init__(self, application):
        static_dirs = {'/static': os.path.join(settings.PROJECT_DIR, 'static')}
        for name, package in Package.ALL.items():
            package_dir = package.get_resource_path('static')
            static_dirs['/%s/static' % name] = package_dir
        super(StaticMiddleware, self).__init__(application, static_dirs)


class ApplicationType(type):
    """A meta class to ensure only one instance of Application exists.
    """
    INSTANCE = None
    def __call__(cls):
        if cls.INSTANCE is None:
            # load all the settings.INSTALLED_PACKAGES
            from rapido.conf.loader import loader
            loader.load()
            cls.INSTANCE = super(ApplicationType, cls).__call__()
        return cls.INSTANCE


class Application(object):
    """The Application class implements a WSGI application. This class is
    responsible to request dispatching, middleware processing, generating
    proper response from the view function return values etc.
    """
    __metaclass__ = ApplicationType

    def __init__(self):
        
        #: list of all the registered middlewares
        self.middlewares = []

        #: url map
        self.url_map = Map()

        #: all the registered view functions
        self.view_funcs = {}

        for pkg in Package.ALL.values():
            self.register_package(pkg)

        # register all the settings.MIDDLEWARE_CLASSES
        for mc in settings.MIDDLEWARE_CLASSES:
            self.middlewares.append(mc())

        # add build only rules for static content
        self.url_map.add(
                Rule('/static/<filename>', endpoint='static', build_only=True))
        self.dispatch = StaticMiddleware(self.dispatch)

    def register_package(self, package):
        """Register a package so that the resources provided by the package
        can be made avilable to the clients.

        :param package: a package instance to be registered.
        """
        for rule, func in package.rules:
            self.url_map.add(rule)
            self.view_funcs[rule.endpoint] = func

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
        """This method will be called after response is successfull created and
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
        raise exception

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
        if isinstance(value, dict):
            return jsonify(value)
        return Response.force_type(value, request.environ)

    def dispatch(self, environ, start_response):
        """The acctual wsgi application. This is not implemented in `__call__`
        so that wsgi middlewares can be applied without losing a reference to 
        the class.
        """
        _local.request = request = Request(environ)
        request.url_adapter = adapter = self.url_map.bind_to_environ(
                                environ, server_name=settings.SERVERNAME)
        try:
            endpoint, args = adapter.match()
            
            request.endpoint = endpoint
            request.view_args = args
            request.view_func = func = self.view_funcs[endpoint]

            response = self.process_request(request)
            if response is None:
                response = self.make_response(func(**args))
        except HTTPException, e:
            response = e
        except Exception, e:
            raise
            response = self.process_exception(request, e)

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
    endpoint is relative to current package. If you wish to refere an endpoint
    from another package prefix it like `package:endpoint` and `module.endpoint`
    to refer from another module in the same package and `.endpoint` to refere 
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
    templates. In that case, if you want to refere global static dir then
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
        reference = endpoint[:endpoint.find(':')]
        endpoint = endpoint[endpoint.find(':')+1:]

    if endpoint == 'static' or endpoint.endswith(':static'):
        ref = request.package if reference is None else reference
        if ref: endpoint = '%s.%s' % (ref, endpoint)
    else:
        ref = reference
        if endpoint.startswith('.'):
            ref = request.endpoint.rsplit('.', 1)[0]
        if not ref:
            ref = request.package
        if ref:
            endpoint = '%s.%s' % (ref, endpoint)
    return request.url_adapter.build(endpoint, values, force_external=external)


def load_template(template):
    """Template loader used as callable for FunctionLoader.
    """
    reference = None
    if ':' in template:
        reference = template[:template.find(':')]
        template = template[template.find(':')+1:]

    if reference is None:
        package = Package.ALL[request.package]
    elif reference:
        package = Package.ALL[reference]
    else:
        package = Package.ALL[None]

    stream = package.get_resource_stream(os.path.join('templates', template))
    filename = stream.name
    try:
        contents = stream.read()#.decode(self.encoding)
    finally:
        stream.close()

    mtime = os.path.getmtime(filename)
    def uptodate():
        try:
            return os.path.getmtime(filename) == mtime
        except OSError:
            return False
    return contents, filename, uptodate


jinja_env = Environment(
    loader=FunctionLoader(load_template),
    autoescape=True,
    extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_'])


jinja_env.globals.update(
        url_for=url_for,
        request=request,
        session=session)


def render_template(template, **context):
    """Render the template from the `templates` folder of the current package
    with the given context.

    If you want to refere to a template from another package, prefix the name
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

    :param template: the name of the template to be rendered.
    :param context: the variables that should be available in the context
                    of the template.

    :returns: string generated after rendering the template
    :raises: :class:`TemplateNotFound` or any other exceptions thrown during
             rendering process
    """
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


