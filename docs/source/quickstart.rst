.. _quickstart:

Quickstart
==========

This guide will help you quickly getting started with *KalaPy*. This assumes
you already have *KalaPy* installed, if not please check the :ref:`installation`
section.

.. note::

    This is just an initial version of quick start guide and not as verbose
    as it should be, but will be improved as it goes...

Create project
--------------

.. sourcecode:: bash

    $ kalapy-admin.py startproject hello

A new project directory `hello` will be created with `admin.py` and `settings.py`
files.


Create package
--------------

.. sourcecode:: bash

    $ cd hello
    $ ./admin.py startpackage foo

A new application package `foo` will be created under the current project
directory with following contents::

    foo/__init__.py
    foo/models.py
    foo/views.py
    foo/tests.py
    foo/static/
    foo/templates/

The `models.py` is where you should define you models and `views.py` is where
you should define you view functions.

You can use the `static` directory to server static contents and the `templates`
directory should hold all the templates for the views.

The application package created here needs to be activated from the `settings`
module of the project created earlier. Open the `settings.py` file and append
`foo` to the list of `INSTALLED_PACKAGES`.

.. note::

    This is is similar to Django but will be changed in future. As the concept
    of package is not exactly the same as application in Django.

    A package can be extended by addon packages. Resources provided by those
    addon packages will be available to the original package (this feature is
    still not implemented though).


Define models
-------------

Models should be defined under `models.py` like this::

    from kalapy import db

    class Article(db.Model):
        title = db.String(size=100, required=True)
        pubdate = db.DateTime(default_now=True)
        text = db.Text(required=True)

        @db.validate(title)
        def validate_title(self, value):
            if len(value) < 5:
                raise db.ValidationError('Title too short...')


    class Comment(db.Model):
        title = db.String(size=100, required=True)
        text = db.Text()
        article = db.ManyToOne(Article)


For more information on model api see :ref:`dal`.

Database setup
--------------

As you defined your models, it's time to setup database to store the model data.
You should configure the database engine from `settings` module via following
settings::

    DATABASE_ENGINE = "sqlite3"
    DATABASE_NAME = "test_hello.sqlite"

Currently, `sqlite3` and `postgresql` backend engines are supported. For simplicity
let you use `sqlite3` for this demo project.

Now as you have configured you database setup, next step is to create database
and required tables for the defined models.

First create the database file:

.. sourcecode:: bash

    $ touch test_hello.sqlite

Then create tables:

.. sourcecode:: bash

    $ ./admin.py database sync

If you want to see the table schema, issue this command:

.. sourcecode:: bash

    $ ./admin.py database info foo

This will print CREATE TABLE statements of all the modules defined in the `foo`
package like this:

.. sourcecode:: sql

    CREATE TABLE "foo_article" (
        "key" INTEGER PRIMARY KEY AUTOINCREMENT,
        "title" VARCHAR(100) NOT NULL,
        "pubdate" DATETIME,
        "text" TEXT NOT NULL
    );
    CREATE TABLE "foo_comment" (
        "key" INTEGER PRIMARY KEY AUTOINCREMENT,
        "title" VARCHAR(100) NOT NULL,
        "text" TEXT,
        "article" INTEGER REFERENCES "foo_article" ("key")
    );

The output varies depending on the database backend you have selected. Use `help`
to see more information on other available commands.

Playing with API
----------------

The `admin.py` script provides two commands to play with the *KalaPy* api.

Start an interactive python shell:

.. sourcecode:: bash

    $ ./admin.py shell

or, run an arbitrary python script in the context of current project

.. sourcecode:: bash

    $ ./admin.py script somescript.py


Let's check with shell::

    >>> from kalapy import db
    >>> from foo.models import *
    >>> article = Article(title='my first article')
    >>> article.text = """
    ... some article
    ... text...
    ... """
    >>> article.save()
    >>> db.commit()
    >>> articles = Article.all().fetch(10)
    >>> for article in articales:
    ...     print article.title


Define views
------------

You should define your view functions inside the `views.py` module like::

    from kalapy import web
    from kalapy.web import request

    @web.route('/')
    def index():
        return """
        <h1>Hello World!</h1>
        """

    @web.route('/foo/<msg>')
    def foo(msg):
        return "Say: %s" % msg

For for information on web component api see :ref:`webapi`.

Start the development server
----------------------------

As you have defined your views, it's time to see it in action. *KalaPy* provides
a simple server for development purpose which can be lauched using the admin
script like:

.. sourcecode:: bash

    $ ./admin.py runserver
     * Running on http://127.0.0.1:8080/
     * Restarting with reloader...

Launch you web browser and go to `http://127.0.0.1:8080/ <http://127.0.0.1:8080/>`_,
you should see your hello world greetings.

