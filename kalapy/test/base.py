"""
kalapy.test.base
~~~~~~~~~~~~~~~~

This module implements TestCase class, the base class for creating test cases.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LICENSE for more details.
"""
import re, unittest

from werkzeug import Client

from kalapy.web import Application, Response


__all__ = ('TestCase',)


#: the wsgi application instance
test_app = Application()


class TestCase(unittest.TestCase):

    def __call__(self, result=None):
        """Overriden to create ``self.client`` attribute, an instance of
        :class:`werkzeug.Client`, which can be used to send virtual requests
        to the test application.
        """
        self.client = Client(test_app, Response)
        super(TestCase, self).__call__(result)

    def assertMatch(self, data, pattern, message=None, flags=0):
        """Tests whether the given pattern matches to the given data.
        """
        if re.search(pattern, data, flags) is None:
            if message is None:
                message = 'No match for %r in the given data' % pattern
            raise self.failureException(message)

