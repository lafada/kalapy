import os, sys

if sys.version_info < (2, 5):
    raise SystemExit("Python 2.5 or later is required")

from setuptools import setup, find_packages

try:
    from babel.messages import frontend as babel
    cmdclasses = {
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog
    }
    message_extractors = {
        'kalapy': [
            ('**.py', 'python', None),
        ],
    }
except ImportError:
    cmdclasses = {}
    message_extractors = {}

# import release meta data (version, author etc.)
execfile(os.path.join("kalapy", "release.py"))

packages = find_packages(exclude=['tests', 'tests.*', 'example', 'example.*'])

setup(
    name='KalaPy',
    version=version,
    url=url,
    license=license,
    author=author,
    author_email=author_email,
    description=description,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Werkzeug>=0.6.2',
        'Jinja2>=2.4.1',
        'Babel>=0.9.5',
        'pytz>=2010h',
        'Pygments>=1.3.1',
        'simplejson>=2.1.1',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    packages=packages,
    include_package_data=True,
    scripts=['bin/kalapy-admin.py'],
    cmdclass=cmdclasses,
    message_extractors=message_extractors,
)

