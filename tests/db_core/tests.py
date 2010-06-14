from kalapy.db.engines import database
from kalapy.test import TestCase

from models import Article


class DBTest(TestCase):

    def tearDown(self):
        database.rollback()

    def test_create_table(self):
        self.assertTrue(database.exists_table(Article._meta.table))

    def test_drop_table(self):
        database.drop_table(Article._meta.table)
        self.assertFalse(database.exists_table(Article._meta.table))
        database.create_table(Article)

    def test_alter_table(self):
        database.alter_table(Article)

    def test_update_records(self):
        a1 = Article(title='title')
        a1.save()

        a1.title = 'something'

        a2 = Article(title='title2')
        a3 = Article(title='title3')

        keys = database.update_records(a1, a2, a3)
        self.assertEqual(keys, [a1.key, a2.key, a3.key])

        a = Article.get(a1.key)
        self.assertTrue(a.title != 'title')

    def test_delete_records(self):
        a1 = Article(title='sometitle')
        k1 = a1.save()

        a2 = Article(title='sometitle2')
        k2 = a2.save()

        keys = database.delete_records(a1, a2)

        self.assertEqual(keys, [k1, k2])

        a = Article.get(k1)

        self.assertTrue(a is None)
        self.assertTrue(a1.key is None)
        self.assertTrue(a2.key is None)
        self.assertTrue(a1.is_dirty and a2.is_dirty)

    def test_select_from(self):
        a = Article(title='some')
        a.save()

        a = Article(title='sometitle')
        a.save()

        res = Article.select('title').filter('title = :title', title='some%').fetch(-1)
        self.assertTrue(len(res) == 2)

    def test_select_count(self):
        a = Article(title='some')
        a.save()

        a = Article(title='sometitle')
        a.save()

        res = Article.all().count()
        self.assertTrue(res == 2)

