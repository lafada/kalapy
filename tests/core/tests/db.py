from kalapy.db.engines import database
from kalapy.test import TestCase

from core.models import *


class DBTest(TestCase):

    def tearDown(self):
        database.rollback()

    def test_create_table(self):
        self.assertTrue(database.exists_table(Article._meta.table))

    def test_drop_table(self):
        database.drop_table(Comment._meta.table)
        self.assertFalse(database.exists_table(Comment._meta.table))
        database.create_table(Comment)

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

        res = Article.select('title').filter('title =', 'some%').fetch(-1)
        self.assertTrue(len(res) == 2)

    def test_select_count(self):
        a = Article(title='some')
        a.save()

        a = Article(title='sometitle')
        a.save()

        res = Article.all().count()
        self.assertTrue(res == 2)


class ModelTest(TestCase):

    def tearDown(self):
        database.rollback()

    def test_inherit_chain(self):
        u1 = User()
        u2 = UserDOB()
        u3 = UserNotes()
        u4 = UserAccount()

        for u in [u1, u2, u3, u4]:
            self.assertTrue(isinstance(u, UserAccount))

    def test_inherit_method_override(self):
        u1 = User()
        u2 = UserDOB()
        u3 = UserNotes()
        u4 = UserAccount()

        for u in [u1, u2, u3, u4]:
            self.assertTrue(u.do_something() == 4)


    def test_model_save(self):
        u1 = User(name="some")
        key = u1.save()
        u2 = User.get(key)
        self.assertTrue(u2.key == u1.key)

    def test_model_save_related(self):

        u1 = User(name="some1")
        ac1 = Account()
        ad1 = Address(street1="s1")
        ad2 = Address(street1="s2")

        u1.address_set.add(ad1, ad2)
        u1.account = ac1

        key = u1.save()

        u2 = u1.get(key)

        self.assertTrue(u2.key == u1.key)
        self.assertTrue(u2.account.key == u1.account.key == ac1.key)
        self.assertTrue(ad1.key == u1.address_set.all().fetch(1)[0].key == \
                                   u2.address_set.all().fetch(1)[0].key)
        self.assertTrue(ad2.key == u1.address_set.all().fetch(1, 1)[0].key == \
                                   u2.address_set.all().fetch(1, 1)[0].key)


    def test_model_delete(self):
        u1 = User(name="some2")
        k1 = u1.save()

        u2 = User(name="some1")
        k2 = u2.save()

        u1.delete()

        u3 = User.get(k1)

        self.assertTrue(u3 is None)

    def test_model_get(self):
        u1 = User(name="some3")
        u2 = User(name="some4")
        k1 = u1.save()
        k2 = u2.save()

        # get single instance
        res = User.get(k1)
        self.assertTrue(isinstance(res, User))

        # get many instances
        res = User.get([k1, k2])
        self.assertTrue(isinstance(res, list))

        # try to get non-existance instance
        res = User.get(3282394802)
        self.assertTrue(res is None)

    def test_model_all(self):
        u1 = User(name="some5")
        u1.save() # ensure at least one record exists

        res = User.all().filter('name ==', u1.name).fetch(-1)
        self.assertTrue(len(res) > 0)

    def test_model_select(self):
        u1 = User(name="some6")
        u1.save() # ensure at least one record exists

        names = User.select('name').filter('name ==', u1.name).fetch(-1)
        self.assertTrue(names[0] == u1.name)


class FieldTest(TestCase):

    def tearDown(self):
        database.rollback()

    def test_field_required(self):
        u = User(name="some", dob='1996-11-04')
        try:
            u.name = None
        except db.ValidationError:
            pass
        else:
            self.fail()

    def test_field_unique(self):

        u = UniqueTest(a='aaa', b='bb', c='cc')
        u.save()

        u2 = UniqueTest(a='aaaa', b='bb', c='dd')
        u3 = UniqueTest(a='aaaaa', b='bb', c='cc')

        try:
            u2.save()
            u3.save()
        except db.IntegrityError:
            pass
        else:
            self.fail()

    def test_field_selection(self):
        u = User(name="some")
        u.lang = 'en_EN'
        try:
            u.lang = 'en_IN'
        except db.ValidationError:
            pass
        else:
            self.fail()

    def test_field_validate(self):
        u = UniqueTest()
        u.a = 'aaaaaaa'
        try:
            u.a = 'aa'
        except db.ValidationError:
            pass
        else:
            self.fail()


class QueryTest(TestCase):

    def tearDown(self):
        database.rollback()

    def test_filter(self):
        for n in list('abcdefghijklmnopqrstuvwxyz'):
            u = User(name=n)
            u.save()

        q = User.all()

        q1 = q.filter('name in', ['a', 'b', 'c'])
        q2 = q.filter('name in', ['d', 'e', 'f'])

        self.assertTrue(q != q1 != q2)

        self.assertTrue(q.count() == 26)
        self.assertEqual([o.name for o in q1.fetch(-1)], ['a', 'b', 'c'])
        self.assertEqual([o.name for o in q2.fetch(-1)], ['d', 'e', 'f'])

    def test_delete(self):

        for n in list('abcdefghijklmnopqrstuvwxyz'):
            u = User(name=n)
            u.save()

        n1 = User.all().count()
        q = User.all().filter('name in', ['a', 'b', 'c'])
        q.delete()
        n2 = User.all().count()

        self.assertTrue(n2 == n1 - 3)

        User.all().delete()
        n2 = User.all().count()

        self.assertTrue(n2 == 0)

    def test_update(self):

        for n in list('abcdefghijklmnopqrstuvwxyz'):
            u = User(name=n)
            u.save()

        q = User.all()

        q1 = q.filter('name in', ['a', 'b', 'c'])
        q2 = q.filter('name in', ['d', 'e', 'f'])

        q1.update(lang='en_EN')
        q2.update(lang='fr_FR')

        n1 = q.filter('lang ==', 'en_EN').count()
        n2 = q.filter('lang ==', 'fr_FR').count()

        self.assertTrue(n1 == 3)
        self.assertTrue(n2 == 3)

