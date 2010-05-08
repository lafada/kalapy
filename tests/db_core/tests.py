from rapido.test import TestCase
from rapido.db.engines import database

from models import Article


class Internal(TestCase):

    def setUp(self):
        super(Internal, self).setUp()
        self.test_create_table()

    def tearDown(self):
        super(Internal, self).tearDown()
        self.test_drop_table()

    def test_create_table(self):
        database.create_table(Article)
        self.assertTrue(database.exists_table(Article._meta.table))

    def test_drop_table(self):
        database.drop_table(Article._meta.table)
        self.assertFalse(database.exists_table(Article._meta.table))

    def test_alter_table(self):
        database.alter_table(Article)

    def test_insert_into(self):
        u = Article(title='title')
        key = database.insert_into(u)
        self.assertTrue(key)

    def test_update_table(self):
        u = Article(title='title')
        u.save()

        u.title = "something"

        key = database.update_table(u)

        u2 = Article.get(u.key)

        self.assertTrue(u.title == u2.title)
        self.assertTrue(u2.title != 'title')

    def test_delete_from(self):
        a = Article(title='sometitle')
        key = a.save()

        database.delete_from(a)
        a2 = Article.get(key)

        self.assertTrue(a2 is None)
        self.assertTrue(a.key is None)

