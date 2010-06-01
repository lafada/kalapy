This is an example project to show you the capability of the framework.
Here are the steps to get started play with it.

1. See admin script help

    $ cd /path/to/example
    $ ./admin.py help
    $ ./admin.py help database
    $ ./admin.py help runserver

2. Initialise the database

    $ touch example.db
    $ ./admin.py database sync

3. Run the developement server

    $ ./admin.py runserver

The include application packages in this example project are direct conversion
from werkzeug examples and Flask examples.

    wiki = werkzeug's simplewiki example
    blog = Flask's Flaskr example

