import os
import difflib

from docutils.core import publish_parts
from jinja2 import Markup

from kalapy import db
from kalapy.web import url_for


class Page(db.Model):
    name = db.String(size=60, required=True, unique=True)

    @property
    def title(self):
        return self.name.replace('_', ' ')

    @classmethod
    def by_name(cls, name):
        page = cls.all().filter('name ==', name).first()
        if page:
            return page.revisions.all().order('-timestamp').first()
        return None

    @classmethod
    def by_revision(cls, revision):
        return Revision.get(revision)


class Revision(db.Model):
    page = db.ManyToOne(Page, reverse_name='revisions')
    timestamp = db.DateTime(default_now=True)
    text = db.Text()
    note = db.String(size=200)

    @property
    def name(self):
        return self.page.name

    @property
    def title(self):
        return self.page.title

    @property
    def time(self):
        return self.timestamp.strftime('%Y-%m-%d %H:%M:%S')

    def render(self):
        return parse_rst(self.text)


def parse_rst(markup):
    parts = publish_parts(
        source=markup,
        writer_name='html4css1',
        settings_overrides={'_disable_config': True})
    return parts['html_body']

class Pagination(object):
    """
    Paginate a query object.
    """

    def __init__(self, query, per_page, page, endpoint):
        self.query = query
        self.per_page = per_page
        self.page = page
        self.endpoint = endpoint
        self._count = None

    @property
    def entries(self):
        return self.query.fetch(self.per_page, (self.page - 1) * self.per_page)

    @property
    def has_previous(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def previous(self):
        return url_for(self.endpoint, page=self.page - 1)

    @property
    def next(self):
        return url_for(self.endpoint, page=self.page + 1)

    @property
    def count(self):
        return self.query.count()

    @property
    def pages(self):
        return max(0, self.count - 1) // self.per_page + 1

