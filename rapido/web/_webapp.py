import types

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


uri_map = Map()


def route(rule, **options):
    def wrapper(func):
        options.setdefault('methods', ('GET',))
        options['endpoint'] = func
        uri_map.add(Rule(rule, **options))
        return func
    return wrapper


def render_template(template, **context):
    pass


def jsonify(obj):
    return Response(json.dumps(obj), mimetype='package/json')


class Request(BaseRequest):
    pass


class Response(BaseResponse):
    pass


class WSGIApplication(object):

    def __init__(self):
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
        local.package = self
        local.request = request = Request(environ)
        local.uri_adapter = adapter = uri_map.bind_to_environ(environ)
        try:
            endpoint, view_args = adapter.match()
            response = self.make_response(endpoint(**view_args))
        except HTTPException, e:
            response = e

        return ClosingIterator(response(environ, start_response),
                [local_manager.cleanup])

    def __call__(self, environ, start_response):
        return self.dispatch(environ, start_response)


def simple_server(host, port, use_reloader=False):
    """Run a simple server for development purpose.
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

