import unittest


__all__ = ('build_suite', 'run_tests')


TEST_MODULE = 'tests'


def build_suite(name):
    """Build test suite for the given name. A name can be either an
    package name or a fully qualified name of the test class or
    a specific test method. For example:

        - hello
            Build a test suite of all the tests found in hello package
        - hello.HelloTest
            Build a test suite for the specific test class
        - hello.HelloTest.test_hello
            Build a test suite for the specific test method

    :returns:
        an instance of `TestSuite`
    """
    names = name.split('.')

    if len(names) > 4:
        raise Exception('Invalid test name %r' % name)

    package = names.pop(0)
    try:
        test_module = __import__('%s.%s' % (package, TEST_MODULE), {}, {}, TEST_MODULE)
    except ImportError:
        raise
        raise Exception('No such package %r' % package)

    suite = unittest.TestSuite()

    if not names:
        suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(test_module))
    else:
        try:
            TestClass = getattr(test_module, names[0])
        except AttributeError:
            raise Exception('No such test class %s.%s' % (package, names[0]))

        if len(names) == 2:
            suite.addTest(TestClass(names[1]))
        else:
            suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestClass))

    return suite


def run_tests(names, verbosity=1):
    """Run unittests for all the test names.

    A name can be either an package name, or fully quilified test class name of
    test class method name. For example:

        - package
            Run all tests found in the given package
        - package.tests.TestClass
            Run all the tests found in the given test class
        - package.tests.TestClass.test_method
            Run the specific test method

    :param names: a sequence of names
    :param verbosity: verbose level
    """

    from rapido.db.engines import database
    from rapido.conf.loader import loader

    database.connect()
    try:
        loader.load() # load all packages
        suite = unittest.TestSuite()
        for name in names:
            suite.addTest(build_suite(name))
        result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    finally:
        database.close()

    return len(result.failures) + len(result.errors)

