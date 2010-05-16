"""
This module implements wsgi complient package and request, response classes.
"""

import sys, types, cgi, traceback

import webob
from webob.exc import *

from _routes import Route, resolve


__all__ = ('Request', 'Response', 'Handler', 'Application', 'HTTPException')


class Request(webob.Request):
    """The request class derived from `webob.Request` to ensure charset is set
    to utf-8.
    """
    def __init__(self, environ):
        super(Request, self).__init__(environ, charset='utf-8')

        
class Response(webob.Response):
    """The response class derived from `webob.Response` to ensure charset is set
    to utf-8.
    """
    
    def __init__(self):
        super(Response, self).__init__(charset='utf-8')
        
    def write(self, content):
        """Write the content to the response.
        """
        #TODO: make sure that the content is converted to string
        self.body_file.write(content)


class HandlerType(type):
    """The meta class for the Handler to ensure all the methods which are routed
    should be referenced as unbound method to the route instance.
    """
    def __new__(cls, name, bases, attrs):
        cls = super(HandlerType, cls).__new__(cls, name, bases, attrs)
        
        for name, item in attrs.items():
            if isinstance(item, types.FunctionType) and \
                    isinstance(getattr(item, 'route', None), Route):
                item.route.handler = getattr(cls, name)
                
        return cls
        

class Handler(object):
    """The base request handler class provides some useful methods to deal with
    request, response as well as errors and redirection.
    
    :param request: an instance of :class:`Request`
    :param response: an instance of :class:`Response`
    """
    
    __metaclass__ = HandlerType
    
    def __init__(self, request, response):
        """Create a new instance of the Handler
        """
        self.request = request
        self.response = response
        
    def write(self, content):
        """Write the content to the response body.
        """
        self.response.body_file.write(content)
        
    def redirect(self, uri):
        """Redirect to the given uri
        """
        raise NotImplementedError('Not implemented yet')


class Application(object):
    """A WSGI compatible package class handles request against the 
    registered routes.
    """
    
    def __init__(self):
        """Create a new instance of the `Application`.
        """
        pass

    def handle(self, request, response):
        """Handle the request resolving against the registered routes.
        
        :param request: An instance of Request
        :param response: An instance of Response
            
        :raises:
            `HTTPException` or exception raised by the handler function
        """
        path = request.path_info
        method = request.method
        
        route = resolve(path, {'REQUEST_METHOD': method})

        if not route:
            raise Exception('not found: %s' % path)

        func = route['handler']
        varargs = route.get('varargs', ())
        keywords = route.get('keywords', {})

        if hasattr(func, 'im_class'):
            controller = func.im_class(request, response)
            varargs = (controller,) + varargs

        func(*varargs, **keywords)
    
    def __call__(self, environ, start_response):
        
        request = Request(environ)
        response = Response()
        
        try:
            self.handle(request, response)
        except HTTPException, e:
            response = e
        except Exception, e:
            lines = ''.join(traceback.format_exception(*sys.exc_info()))
            response.body = '<pre>%s</pre>' % cgi.escape(lines, quote=True)
            
        return response(environ, start_response)

