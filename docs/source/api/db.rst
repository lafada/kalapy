.. _dal:

.. currentmodule:: rapido.db

Database Abstraction Layer
==========================

An unique database abstraction layer (DAL) inspired of OpenERP and Django ORM. 
The DAL API is designed such that it can work with any kind of database management 
system, be it an RDBMS or NoSQL, or even can be used with OpenERP.

A programming model should be declared as a subclass of :class:`Model`,
declaring properties as any of :class:`Field` subclass. So if you want to
publish an article with title, text, and publishing date, you would do it 
like this::

    class Article(db.Model):
        title = db.String(size=100, required=True)
        pubdate = db.DateTime(default_now=True)
        text = db.Text(required=True)

You can then create new Article, like this::

    article = Article(title='My Article')
    article.text = "some text"
    article.save()
    db.commit()

You can query your articles using query interface provided, like::

    articles = Article.all().filter('pubdate >= :pubdate', 
                                     pubdate=somedate) \\
                            .order('-pubdate')
    for article in articles:
        print article.title

The inputs will be validated according to the properties to which it is being
assigned. That is, a `db.DateTime` property can only be assigned a valid datetime
value (real python datetime.datetime, or string representation of datetime).
Beside that you can also validate input using `db.validate` decorator, 
like::

    class Article(db.Model):
        title = db.String(size=100, required=True)
        pubdate = db.DateTime(default_now=True)
        text = db.Text(required=True)

        @db.validate(title)
        def validate_title(self, value):
            if len(value) < 5:
                raise db.ValidationError('Title too short...')

You can also relate models using any of the provided reference fields to 
represent many-to-one, one-to-one, one-to-many or many-to-many relationships
among them. For example::

    class Comment(db.Model):
        title = db.String(size=100, required=True)
        text = db.Text()
        article = db.ManyToOne(Article)

A reverse lookup field named `comment_set` will be automatically created
in the `Article` model. Reference properties can be accessed like this::

    comment = Comment.get(key)
    print comment.article.title

    article = Article.get(key)
    for comment in article.comment_set.all().fetch(-1):
        print comment.title


Model
-----

.. autoclass:: Model
    :members:
    
.. autofunction:: get_model

.. autofunction:: get_models


Fields
------

.. autoclass:: FieldError
    :members:
    
.. autoclass:: ValidationError
    :members:
    
.. autoclass:: Field
    :members:
    
.. autoclass:: String
    :members:

.. autoclass:: Text
    :members:
    
.. autoclass:: Integer
    :members:
    
.. autoclass:: Float
    :members:
    
.. autoclass:: Decimal
    :members:
    
.. autoclass:: Boolean
    :members:
    
.. autoclass:: Date
    :members:
    
.. autoclass:: Time
    :members:
    
.. autoclass:: DateTime
    :members:
    
.. autoclass:: Binary
    :members:
    
    
Relational Fields
-----------------

.. autoclass:: ManyToOne
    :members:
    
.. autoclass:: OneToOne
    :members:
    
.. autoclass:: OneToMany
    :members:
    
.. autoclass:: ManyToMany
    :members:

Query
-----

Once you have your models, you need a way to retrieve stored model instances
from the database. As the DAL is designed to be DBMS independent it is quite
difficult to use SQL for this purpose. To deal with this issue, DAL provides
a generic query interface which is more pythonic. It also guards you from some
common vulnerabilities like SQL injection.

A :class:`Query` instance queries over instances of :class:`Model`.

You can create a :class:`Query` instance with a model class like this::

    users = Query(User).filter('name = :name', name='some') \\
                       .order('-name') \\
                       .fetch(10)

This is equivalent to:

.. sourcecode:: sql

    SELECT * FROM 'user' WHERE 'name' like '%some%' ORDER BY 'name' DESC LIMIT 10

The query string accepted by filter method is simple pythonic expression where 
LHS is a name of a field in the give model and RHS is a placeholder for the named 
parameter bound to the provided keyword arguments.

The exact syntax of the query statement should be like:

.. sourcecode:: antlr-python

    statement   ::=     expression (("and" | "or") expression)*
    expression  ::=     identifier operator ":"identifier
    identifier  ::=     ("a"..."z"|"A"..."Z"|"_")("a"..."z"|"A"..."Z"|"0".."9"|"_")*
    operator    ::=     "=" | "==" | "!=" | ">" | "<" | ">=" | "<=" | ["not"] "in"

The query expression supports following operators:

    ============= ==========================
    Operator      Meaning
    ============= ==========================
    `=`           case insensitive match
    `==`          exact match
    `>`           greater then
    `<`           less then
    `>=`          greater then or equal to
    `<=`          less then or equal to
    `!=`          not equal to
    `in`          within the given items
    `not in`      not within the give items
    ============= ==========================

Here are few valid query statements::

    "name = :name and age >= :age"
    "country == :country or lang == :lang"

For convenience, all of the filtering and ordering methods return "self", so
you can chain method calls like this::

    users = Query(User).filter('name = :name and age >= :age', 
                                name='some', age=18) \\
                       .filter('country == :country or lang in :lang',
                                country='in', lang=['en', 'hi', 'gu']) \\
                       .order('-country').fetch(100)

This is equivalent to:

.. sourcecode:: sql

    SELECT * FROM 'user' WHERE
        ('name' like '%some%' AND 'age' >= 18)
        AND
        ('country' = 'in' OR 'lang' in ('en', 'hi', 'gu'))
    ORDER BY 'country' DESC
    LIMIT 100

Proceed with the :class:`Query` documentation for more details...

.. autoclass:: Query
    :members:


Helpers
-------

.. autofunction:: meta

.. autofunction:: validate

.. autofunction:: unique

