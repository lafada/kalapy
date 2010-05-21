import re, os, sys, types

try:
    import json
except ImportError:
    import simplejson as json


from werkzeug import (
    Request as BaseRequest,
    Response as BaseResponse
)

from werkzeug import Local, LocalManager, ClosingIterator
from werkzeug.routing import Rule, Map
from werkzeug.exceptions import HTTPException

from jinja2 import Environment, FileSystemLoader, Markup, escape

from rapido.conf import settings


#: uri routing map
uri_map = Map()


def route(rule, **options):
    """A decorator to define a routing rule for request handler functions.
    
    :param rule: rule pattern
    :param options: rule options, like methods, defaults etc.
    """
    def wrapper(func):
        options.setdefault('methods', ('GET',))
        options['endpoint'] = func
        uri_map.add(Rule(rule, **options))
        return func
    return wrapper


def uri(path, **names):
    """Generate uri for the given path and names.
    
    :param path: uri path
    :param names: names to be used to generate uri
    """
    pass


def redirect(path, **names):
    """Redirect to the uri generated with the given path and names.
    
    :param path: uri path
    :param names: names to be used to generate uri
    """
    pass


jinja_env = Environment(
        loader=FileSystemLoader(settings.PROJECT_DIR),
        autoescape=True,
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_'])

#TODO: update jinja_env.globals
#TODO: update jimja_env.filters

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
    base = os.path.dirname(sys.modules[request.endpoint.__module__].__file__)
    template_path = os.path.abspath(os.path.join(base, template))
    template_path = os.path.relpath(template_path, settings.PROJECT_DIR)
    
    return jinja_env.get_template(template_path).render(context)


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

    
class WSGIApplication(object):
    """WSGIApplication is responsible to dispatch requests and return proper
    response and ensures that all the request specific cleanup is done when
    the response is properly servered.
    """

    def __init__(self):
        #TODO: register static data middleware
        #TODO: register settings.MIDDLEWARE
        pass

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
        raise ValueError('Handler has returned unsupported type %r' % type(rv).__name__)

    def dispatch(self, environ, start_response):
        local.request = request = Request(environ)
        local.uri_adapter = adapter = uri_map.bind_to_environ(environ)
        try:
            endpoint, args = adapter.match()
            request.endpoint = endpoint
            request.endpoint_args = args
            response = self.make_response(endpoint(**args))
        except HTTPException, e:
            response = e

        return ClosingIterator(response(environ, start_response),
                [local_manager.cleanup])

    def __call__(self, environ, start_response):
        return self.dispatch(environ, start_response)


def simple_server(host='127.0.0.1', port=8080, use_reloader=False):
    """Run a simple server for development purpose.
    
    :param host: host name
    :param post: port number
    :param use_reloader: whether to reload the server if any of the loaded 
                         module changed.
    """
    from werkzeug import run_simple
    from rapido.conf import settings
    from rapido.conf.loader import loader

    # load packages
    loader.load()
    
    # create a wsgi package
    package = WSGIApplication()
    debug = settings.DEBUG

    run_simple(host, port, package, use_reloader=use_reloader, use_debugger=debug)


local = Local()
local_manager = LocalManager([local])

request = local('request')

