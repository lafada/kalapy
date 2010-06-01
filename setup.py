"""
"""
from setuptools import setup


setup(
    name='Rapido',
    version='0.5',
    url='http://github.com/cristatus/rapido/',
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
    packages=['rapido', 'rapido.admin', 'rapido.admin.commands', 'rapido.conf',
              'rapido.contrib', 'rapido.contrib.sessions',
              'rapido.db', 'rapido.db.engines',
              'rapido.db.engines.sqlite3',
              'rapido.db.engines.postgresql',
              'rapido.db.engines.dummy',
              'rapido.web'],
    include_package_data=True,
    scripts = ['bin/rapido-admin.py'],
)
