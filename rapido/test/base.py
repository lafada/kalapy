import unittest


__all__ = ('TestCase', 'WebTestCase')


class TestCase(unittest.TestCase):
    pass


class WebTestCase(TestCase):
    pass

