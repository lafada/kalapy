"""
"""
from setuptools import setup
from babel.messages import frontend as babel

import kalapy


setup(
    name='KalaPy',
    version=kalapy.__version__,
    url='http://github.com/cristatus/kalapy/',
    license='BSD',
    author='Amit Medapara',
    author_email='mendapara.amit@gmail.com',
    description='A highly scalable rapid web application framework',
    #long_description=__doc__,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Werkzeug>=0.6.2',
        'Jinja2>=2.4.1',
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
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    packages=['kalapy', 'kalapy.admin', 'kalapy.admin.commands', 'kalapy.conf',
              'kalapy.contrib', 'kalapy.contrib.sessions',
              'kalapy.db', 'kalapy.db.engines',
              'kalapy.db.engines.sqlite3',
              'kalapy.db.engines.postgresql',
              'kalapy.db.engines.dummy',
              'kalapy.web'],
    include_package_data=True,
    scripts = ['bin/kalapy-admin.py'],
    cmdclass = {
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog
    },
    message_extractors = {
        'kalapy': [
            ('**.py', 'python', None),
        ],
    },
)

