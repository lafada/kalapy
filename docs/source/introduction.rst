Introduction
================================================================================

*Rapido* is a web application framework for `Python`_ based on `Werkzeug`_ and 
`Jinja2`_. It provides it's own unique `Database Abstraction Layer <dal>`_, 
localisation via `Babel`_ and `pytz`_ and more...

This is just a preview release. The development is still under alpha stage and
API might change during this period. I welcome your useful suggestions/thoughts
about how to improve it and how it should look like.

At the moment it looks some what similar to `Django`_, but it is only so to get
started quickly. The intention is to implement a framework that combines power
of `OpenObject`_ and `Django`_. Let's see how it goes...

.. _Werkzeug: http://werkzeug.pocoo.org/
.. _Jinja2: http://jinja.pocoo.org/2/
.. _Babel: http://babel.edgewall.org/
.. _pytz: http://pytz.sourceforge.net/
.. _Python: http://python.org/
.. _Django: http://djangoproject.org/
.. _OpenObject: https://launchpad.net/openobject/


Intentions & Goals
------------------

* localisation (using babel, pytz)
* unit tests
* documentation
* google app engine support
* mysql support
* packages (are not applications)
    - per package settings file
    - support for extending an existing package with addon packages
    - resources provided by addon package should get preference over
      original package
* auto views (using GWT or Dojo), can be mixed with normal html
* admin interface
    - activate/deactivate packages
    - configuration

Target Audience
---------------

todo

