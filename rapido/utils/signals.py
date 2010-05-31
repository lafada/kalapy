"""This module implements simple signal dispatcher.

Connecting a signal is as easy as using a `signals.connect` decorator
with signal name on a handler function. The signal can be fired with 
`signals.send` method along with params if any.

For example:

>>> @signals.connect('onfinish')
>>> def on_finish_1(state):
>>>     pass

>>> @signals.connect('onfinish')
>>> def on_finish_2(state):
>>>     pass

The signal can be fired like this:

>>> signals.send('onfinish', state=1)

In this case both the handlers connected to the 'onfinish' signal will 
be fired.
"""
import types, inspect, weakref


__all__ = ('Signal', 'connect', 'disconnect', 'send')


class Signal(object):
    """Signal class caches all the registered handlers in WeakValueDictionary
    so that handlers can be automatically garbage collected if the reference
    to the handler is the only reference.
    
    :param name: name for the signal
    """
    def __init__(self, name):
        """Create a new Signal instance with the given name.
        """
        self.name = name
        self.registry = weakref.WeakValueDictionary()
        
    def make_id(self, handler):
        if hasattr(handler, 'im_func'):
            return id(handler.im_self), id(handler.im_func)
        return id(handler)

    def connect(self, handler):
        """Connect the given handler to the signal. The handler must be a 
        function.

        :param handler: a signal handler

        :return: returns the handler itself
        :raises: 
            `TypeError`: if handler is not a function
        """
        if not isinstance(handler, types.FunctionType):
            raise TypeError('Signal handler must be a function')
        id = self.make_id(handler)
        if id not in self.registry:
            self.registry[id] = handler
        return handler

    def disconnect(self, handler):
        """Manually disconnect the given handler if it is registered with
        this signal.

        By default, the handler will be removed automatically from the signal
        registry if it is the only reference remained.

        :param handler: the handler function
        """
        id = self.make_id(handler)
        self.registry.pop(id, None)

    def send(self, *args, **kw):
        """Fire the signal.

        All handlers registered with this signal instance will be called passing
        the given *args nad **kw

        :param args: to be passed to signal handlers
        :param kw: to be passed to signal handlers

        :returns: list of results returned by all the handlers
        """
        result = []
        for handler in self.registry.values():
            result.append(handler(*args, **kw))
        return result


registry = {}

def connect(signal):
    """A decorator to connect a function to the specified signal.

    >>> @signals.connect('onfinish')
    >>> def on_finish_1(state):
    >>>     pass

    :param signal: name of the signal
    """
    def wrapper(func):
        registry.setdefault(signal, Signal(signal)).connect(func)
        return func
    return wrapper

def disconnect(signal, handler=None):
    """If handler is given then disconnect the handler from the specified signal
    else disconnect all the handlers of the given signal.

    >>> signals.disconnect('onfinish', on_finish_1)
    >>> signals.dispatcher('onfinish')

    :param signal: name of the signal
    :param handler: a signal handler
    """
    if signal not in registry:
        return
    if handler:
        registry[signal].disconnect(handler)
        return
    registry[signal].registry.clear()
    del registry[signal]


def send(signal, *args, **kw):
    """Fire the specified signal.

    The signal handlers will be called with the given *args and **kw.

    >>> signals.send('onfinish', state=1)

    :param args: to be passed to the signal handlers
    :param kw: to be passed to the signal handlers

    :returns: list of the results of all the signal handlers
    """
    result = []
    if signal in registry:
        result.extend(registry[signal].send(*args, **kw))
    return result

