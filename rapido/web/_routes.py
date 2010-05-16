"""This module implements simple routing system. The route patter is just a
simple string with keywords prefixed with ':' or a generic pattern ending with
'/.*'. The keywords can be validated using regular expression or can be converted
by providing converter function.

Here is an example:

>>> @route('/user/.*')
>>> def default(*args):
>>>     ...
>>>
>>> @route('/user/:limit/:offset', limit='\d\d', offset=int)
>>> def find(limit, offset):
>>>     ...
>>> 
>>> @route('/user/:key', 'GET')
>>> def get(key):
>>>     pass
>>> 
>>> 
>>> @route('/user/:key', 'POST', 'PUT')
>>> def save(key=None):
>>>     pass
>>> 
>>> 
>>> @route('/user/:key', 'POST', 'DELETE')
>>> def delete(key):
>>>     pass

The rule for `default` will be matched if no other suitable route found.
The rule for `find` will be matched if `limit` and `offset` validates accordingly.
The rule for `get` will be matched only if request is GET
The rule for `save` will be matched only if request is either POST or PUT
The rule for `delete` will be matched only if request is either POST or DELETE

As shown in the case of `default` you can validate/convert keywords by providing
regular expression or a callable.
"""

import re


__all__ = ('RouteException', 'Route', 'Mapper', 'route', 'resolve')


METHODS = ('GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'TRACE')


class RouteException(Exception):
    """The base exception for any routing related errors.
    """
    pass


class Route(object):
    """A Route represents one URI pattern.
    
    `pattern`
        A Route pattern having `keywords` placeholder in the format '/:name' 
        and optionally `varargs` placeholder at the end in the format `/.*`.
        
    `handler`
        The handler function
        
    `*methods`
        A sequence of http methods this rule applis to. If not given it 
        defaults to GET method.
        
    `**validators`
        validators/convertors for the keyword placeholders. A validator can 
        be a regular expression string to validate or a callable to convert 
        the matched keyword.
    """
    
    def __init__(self, pattern, handler, *methods, **validators):
        self.pattern = pattern
        self.regexp = self.compile_pattern(pattern)
        self.handler = handler
        self.has_varargs = re.match('/\.\*$', pattern)
        
        methods = [m.strip().upper() for m in methods]

        for m in methods:
            if m not in METHODS:
                raise RouteException('Invalid method %r' % m)

        self.methods = methods or ['GET']
        self.validators = validators

    def compile_regex(self, s):
        """Compile the given string to regular expression.
        """
        if not s.startswith('^'):
            s = '^%s' % s
        if not s.endswith('$'):
            s = '%s$' % s
        return re.compile(s)

    def compile_pattern(self, s):
        """Compile the given pattern string to regular expression.
        """
        s = s.strip()
        s = re.sub(':([a-zA-Z_][a-zA-Z_]*)', r'(?P<\1>[^/]+)', s)
        s = re.sub('/\.\*', '(?P<varargs>.*)', s)
        return self.compile_regex(s)

    def match(self, path, environ=None):
        """Match the given path with this rule. The environ if provided will be
        used to determine request method.
        
        :param path: the path string
        :param environ: wsgi environment
            
        :returns:
            None if not matched else returns a dict with handler, keywords and
            varargs information.
        """
        environ = environ or {}
        method = environ.get('REQUEST_METHOD', 'GET')

        if method not in self.methods:
            return None

        match = self.regexp.match(path)
        if not match:
            return None

        params = match.groupdict()
        varargs = params.pop('varargs', None)

        for name, validator in self.validators.items():
            if name in params:
                value = params[name]
                if isinstance(validator, basestring): # if regex validation
                    reg = self.compile_regex(validator)
                    if not reg.match(value):
                        return None
                elif callable(validator): # if callable validator
                    try:
                        params[name] = validator(value)
                    except:
                        return None

        result = dict(handler=self.handler)
        
        if params:
            result['keywords'] = params

        if varargs:
            result['varargs'] = varargs.strip('/').split('/')

        return result
        

class Mapper(object):
    """Mapper holds the list of routes and resolves the path against this list.
    """
    def __init__(self):
        """Create a new instance of Mapper.
        """
        self.routes = []

    def resolve(self, path, environ=None):
        """Resolve the given path against all the registered routes. This 
        method takes care of best matching route giving `varargs` rule least
        preference.
        
        :param path: the path string
        :param environ: wsgi environment
            
        :returns:
            None if path doesn't match to any of the registered route else 
            returns a dict of matching info returned by the matched route.
        """
        result = None
        for route in self.routes:
            match = route.match(path_info, environ)
            if match and route.has_varargs:
                result = match
                continue
            if match:
                return match
        return result

    def connect(self, pattern, handler, *methods, **validators):
        """Connect a route for the given pattern and handler function.
        
        :param patter: the rule pattern
        :param handler: the handler function
        :param methods: sequence of http methods
        :param validators: validators/convertors to keyword placeholders
        
        :returns:
            an instance of :class:`Route`
        """
        route = Route(pattern, handler, *methods, **validators)
        self.routes.append(route)
        return route


ROUTES = Mapper()

def route(pattern, *methods, **validators):
    """A decorator to connect a handler function to the routing map with the
    given pattern, methods and validators.
    
    For example:
        
    >>> @route('/user/:limit/:offset', 'GET', limit='\d\d', offset=int)
    >>> def find(limit, offset):
    >>>     ...
    
    :param pattern: the rule pattern
    :param methods: sequence of http methods allowed
    :param validators: validators/convertors for the keyword placeholders
    """
    def wrapper(func):
        func.route = ROUTES.connect(pattern, func, *methods, **validators)
        return func
    return wrapper

resolve = ROUTES.resolve


if __name__ == "__main__":

    @route('/default/.*')
    def default(*args):
        pass

    @route('/find/:limit/:offset', limit='\d\d', offset=int)
    def find(limit, offset, *args):
        pass

    @route('/get/:key')
    def get(key):
        pass

    @route('/save/:key', 'POST', 'PUT')
    def save(key):
        pass

    print resolve('/save/1', {'REQUEST_METHOD': 'POST'})
    print resolve('/find/10/0', {'REQUEST_METHOD': 'GET'})
    print resolve('/find/asd/0', {'REQUEST_METHOD': 'GET'})
    print resolve('/default/a/b/c/d')

