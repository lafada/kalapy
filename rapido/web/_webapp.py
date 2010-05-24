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
    Href, 
    redirect as _redirect
)

from werkzeug.routing import Rule, Map, Submount
from werkzeug.exceptions import HTTPException, NotFound

from jinja2 import Environment, FileSystemLoader, Markup, escape

from rapido.conf import settings
from rapido.utils.local import local, local_manager


__all__ = ('route', 'uri', 'redirect', 'render_template', 'jsonify', 'request', 
           'simple_server', 'Request', 'Response', 'WSGIApplication',
           'HTTPException', 'NotFound', 'Markup', 'escape')


#: uri routing map
uri_map = Map()

#: cache for endpoint and views
view_funcs = {}


def add_rule(rule, func=None, package_name=None, **options):
    options.setdefault('methods', ('GET',))

    if func is not None:
        package_name = func.__module__.split('.', 1)[0]
        endpoint = options.setdefault('endpoint', '%s.%s' % (
            func.__module__, func.__name__))
    else:
        endpoint = options.get('endpoint')

    if not endpoint:
        raise ValueError('No enough options provided.')

    appopt = settings.PACKAGE_OPTIONS.get(package_name, {})
    subdomain = appopt.get('subdomain')
    submount = appopt.get('submount')
    
    if subdomain:
        options.setdefault('subdomain', subdomain)

    rule = Rule(rule, **options)
    if submount:
        rule = Submount(submount, [rule])

    view_funcs[endpoint] = func
    uri_map.add(rule)


def route(rule, **options):
    """A decorator to define a routing rule for request handler functions.
    
    :param rule: rule pattern
    :param options: rule options, like methods, defaults etc.
    """
    def wrapper(func):
        add_rule(rule, func, **options)
        return func
    return wrapper


def uri(path, **names):
    """Generate uri for the given path or endpoint and names.
    
    >>> uri('some/thing', name='some')
    'some/thing?name=some'
    >>> uri('/some/thing' name='some')
    '/some/thing?name=some'
    >>> uri('hello.web.find', key='somekey', name='name')
    '/find/somekey?name=name'
    >>> uri('static', filename='css/some.css')
    '/static/css/some.css'
    >>> uri('hello.static', filename='css/some.css')
    '/hello/static/css/some.css'
    
    :param path: path or endpoint
    :param names: names to be used to generate uri
    """
    if path in view_funcs:
        return local.uri_adapter.build(path, names)
    return Href(path)(**names)


def redirect(path, **names):
    """Redirect to the uri generated with the given path and names.
    
    :param path: uri path
    :param names: names to be used to generate uri
    """
    return _redirect(uri(path, **names))


def render_template(template, **context):
    """Render the template with the given context.
    
    The template is a relative path to the template from the module where the
    :func:`render_template` is called. For example::
        
        @web.route('/hello')
        def hello():
            return web.render_template('templates/hello.html')
        
        @web.route('/hello2')
        def hello2():
            return web.render_template('../some/templates/hello.html')
        
    :param template: template path
    :param context: template context variables
    
    :returns: rendered string
    """
    view_func = view_funcs[request.endpoint]
    base = os.path.dirname(sys.modules[view_func.__module__].__file__)
    template_path = os.path.abspath(os.path.join(base, template))
    template_path = os.path.relpath(template_path, settings.PROJECT_DIR)
    
    return local.package.jinja_env.get_template(template_path).render(context)


def jsonify(obj):
    """Convert the given object into json string as the body of an instance of
    :class:`Response` with mimetype set to `package/json`.
    
    :param obj: an object that should be converted to json string
    :returns: an instance of :class:`Response`
    """
    return Response(json.dumps(obj), mimetype='package/json')


class Request(BaseRequest):
    """The Request class
    """
    pass


class Response(BaseResponse):
    """The Response class
    """
    default_mimetype = 'text/html'


class StaticMiddleware(SharedDataMiddleware):

    def __init__(self, package):
        static_dirs = {'/static': os.path.join(settings.PROJECT_DIR, 'static')}
        add_rule('/static/<filename>', endpoint='static', build_only=True)

        for package in settings.INSTALLED_PACKAGES:
            package_dir = os.path.join(settings.PROJECT_DIR, package)
            if os.path.exists(package_dir):
                static_dirs['/%s/static' % package] = os.path.join(package_dir, 'static')
                add_rule('/%s/static/<filename>' % package, 
                        endpoint='%s.static' % package, package_name=package, build_only=True)
        super(StaticMiddleware, self).__init__(package, static_dirs)


class WSGIApplicationType(type):
    """Meta class to ensure singleton WSGIApplication
    """
    INSTANCE = None
    def __call__(cls):
        if cls.INSTANCE is None:
            # load settings.INSTALLED_PACKAGES
            from rapido.conf.loader import loader
            loader.load()
            # initialize WSGIApplication
            cls.INSTANCE = super(WSGIApplicationType, cls).__call__()
        return cls.INSTANCE


class WSGIApplication(object):
    """WSGIApplication is responsible to dispatch requests and return proper
    response and ensures that all the request specific cleanup is done when
    the response is properly servered.
    """

    __metaclass__ = WSGIApplicationType

    def __init__(self):
    
        #TODO: register settings.MIDDLEWARES
        
        self.dispatch = StaticMiddleware(self.dispatch)
        local.package = self

        self.jinja_env = Environment(
            loader=FileSystemLoader(settings.PROJECT_DIR),
            autoescape=True,
            extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_'])

    def make_response(self, rv):
        if rv is None:
            raise ValueError('Handler function must return a response')
        if isinstance(rv, Response):
            return rv
        if isinstance(rv, basestring):
            return Response(rv)
        if isinstance(rv, tuple):
            return Response(*tuple)
        if isinstance(rv, dict):
            return jsonify(rv)
        if isinstance(rv, types.GeneratorType):
            return Response(rv)
        return Response.force_type(rv, request.environ)

    def dispatch(self, environ, start_response):
        local.package = self
        local.request = request = Request(environ)
        local.uri_adapter = adapter = uri_map.bind_to_environ(
                                environ, server_name=settings.SERVERNAME)
        try:
            endpoint, args = adapter.match()
            request.endpoint = endpoint
            request.endpoint_args = args
            view_func = view_funcs[endpoint]
            response = self.make_response(view_func(**args))
        except HTTPException, e:
            response = e

        return ClosingIterator(response(environ, start_response),
                [local_manager.cleanup])

    def __call__(self, environ, start_response):
        return self.dispatch(environ, start_response)


#: context local :class:`Request` instance
request = local('request')


def simple_server(host='127.0.0.1', port=8080, use_reloader=False):
    """Run a simple server for development purpose.
    
    :param host: host name
    :param post: port number
    :param use_reloader: whether to reload the server if any of the loaded 
                         module changed.
    """
    from werkzeug import run_simple
    from rapido.conf import settings
    
    # create a wsgi package
    package = WSGIApplication()
    debug = settings.DEBUG

    run_simple(host, port, package, use_reloader=use_reloader, use_debugger=debug)

