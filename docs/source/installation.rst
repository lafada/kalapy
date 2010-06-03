.. _installation:

Installation
============

This guide with help you to properly install *Rapido* and all it's dependencies.


.. note::

    This is an initial version of installation guide and doesn't provide much
    information on some topics, but will be improved as it goes...


Prerequisite
------------

* Python >= 2.5
* Werkzeug >= 0.6.2
* Jinja2 >= 2.4.1
* simplejson >= 2.1.1 (not required for py2.6)
* Pygments >= 1.3.1 (optional, to see colourful output on terminal)

I assume you already have Python installed on you system.

virtualenv
----------

Follow this link more information on `virtualenv`_.

I assume you are using *ubuntu* (mine is ubuntu lucid with python 2.6).
Issue following commands if you haven't installed virtualenv package yet.

.. sourcecode:: bash

    $ sudo apt-get install python-vertualenv
    
Now create your virtualenv directory, like:

.. sourcecode:: bash

    $ virtualenv /path/to/your/env
    New python executable in env/bin/python
    Installing setuptools............done.
    
Now, you should activate it, whenever you work with it.

.. sourcecode:: bash

    $ . env/bin/activate
    
Now you can just enter the following command to get Rapido installed in
your virtualenv::

    $ easy_install Rapido

After installed, type following command to see whether it is properly installed
or not:

.. sourcecode:: bash

    $ rapido-admin.py
    Usage: rapido-admin.py <command> [options] [args]

    options:

      -h --help    show help text and exit
         --version show version information and exit

    available commands:

      startproject

    use "rapido-admin.py help <command>" for more details on a command

.. _virtualenv: http://pypi.python.org/pypi/virtualenv/

System Wide Installation
------------------------

This is not recommended, as Rapido is still unstable, under heavy development
and not tested well.

.. sourcecode:: bash

    $ sudo easy_install Rapido


Playing with Source
-------------------

*Rapido* is an open source project released under BSD license. You can grab
the latest sources from `github.com <http://github.com/cristatus/Rapido>`_.

