from kalapy.test import TestCase
from kalapy.utils import signals


class SignalTest(TestCase):

    def test_connect(self):

        @signals.connect('foo-signal')
        def foo_handler1(bar):
            return 1, bar

        @signals.connect('foo-signal')
        def foo_handler2(bar):
            return 2, bar

        @signals.connect('foo-signal')
        def foo_handler3(bar):
            return 3, bar

        assert signals.send('foo-signal', bar='BAR') == [(1, 'BAR'), (2, 'BAR'), (3, 'BAR')]

    def test_disconnect(self):

        @signals.connect('foo-signal')
        def foo_handler1(bar):
            return bar

        @signals.connect('foo-signal')
        def foo_handler2(bar):
            return bar

        @signals.connect('foo-signal')
        def foo_handler3(bar):
            return bar

        assert signals.send('foo-signal', bar='BAR') == ['BAR', 'BAR', 'BAR']
        signals.disconnect('foo-signal')
        assert signals.send('foo-signal', bar='FOO') == []


