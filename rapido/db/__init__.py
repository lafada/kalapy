"""
rapido.db
~~~~~~~~~

An unique database abstraction layer (DAL) inspired by openerp and django
orm. The DAL api is designed such that it can work with any kind of database
management system, be it an RDBMS or NoSQL, or even can be used with OpenERP.

A programming model should be declared as a subclass of :class:`db.Model`,
declaring properties as any of :class:`db.Field` subclass. So if you want to
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

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LICENSE for more details.
"""
from rapido.db.engines import DatabaseError, IntegrityError, commit, rollback

from fields import *
from reference import *
from model import *
from query import *
from helpers import *

# remove module references to hide them from direct outside access
map(lambda n: globals().pop(n), ['engines', 'model', 'fields', 'query', 'reference', 'helpers'])

