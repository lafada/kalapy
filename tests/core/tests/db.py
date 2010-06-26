from kalapy.conf import settings
from kalapy.db.engines import database
from kalapy.test import TestCase

from core.models import *

class TestCase(TestCase):

    def setUp(self):
        if settings.DATABASE_ENGINE == 'gae':
            from kalapy.admin.commands.db import DBCommand
            cmd = DBCommand()
            models, __ = cmd.get_models()
            models.reverse()
            for m in models:
                m.all().delete()
        else:
            database.rollback()

class DBTest(TestCase):

    def test_create_table(self):
        if settings.DATABASE_ENGINE == "gae":
            return
        self.assertTrue(database.exists_table(Article._meta.table))

    def test_drop_table(self):
        if settings.DATABASE_ENGINE == "gae":
            return
        database.drop_table(Comment._meta.table)
        self.assertFalse(database.exists_table(Comment._meta.table))
        database.create_table(Comment)

    def test_alter_table(self):
        if settings.DATABASE_ENGINE == "gae":
            return
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

    def test_fetch(self):
        a = Article(title='some')
        a.save()

        a = Article(title='sometitle')
        a.save()

        res = Article.select('title').filter('title in', ('some', 'sometitle')).fetch(-1)
        self.assertTrue(len(res) == 2)

    def test_count(self):
        a = Article(title='some')
        a.save()

        a = Article(title='sometitle')
        a.save()

        res = Article.all().count()
        self.assertTrue(res == 2)


class ModelTest(TestCase):

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


class QueryTest(TestCase):

    def test_filter(self):
        for n in list('abcdefghijklmnopqrstuvwxyz'):
            u = User(name=n)
            u.save()

        q = User.all().order('name')

        q1 = q.filter('name in', ['a', 'b', 'c'])
        q2 = q.filter('name in', ['d', 'e', 'f'])

        self.assertTrue(q != q1 != q2)

        self.assertTrue(q.count() == 26)
        r1 = [o.name for o in q1.fetch(-1)]
        r2 = ['a', 'b', 'c']
        self.assertEqual(r1, r2)
        r1 = [o.name for o in q2.fetch(-1)]
        r2 = ['d', 'e', 'f']

        self.assertEqual(r1, r2)

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


class FieldTest(TestCase):

    def test_required(self):
        u = User(name="some", dob='1996-11-04')
        try:
            u.name = None
        except db.ValidationError:
            pass
        else:
            self.fail()

    def test_unique(self):
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

    def test_selection(self):
        u = User(name="some")
        u.lang = 'en_EN'
        try:
            u.lang = 'en_IN'
        except db.ValidationError:
            pass
        else:
            self.fail()

    def test_validate(self):
        u = UniqueTest()
        u.a = 'aaaaaaa'
        try:
            u.a = 'aa'
        except db.ValidationError:
            pass
        else:
            self.fail()

    def test_cascade(self):
        u1 = User(name="u1")
        u2 = User(name="u2")
        u3 = User(name="u3")
        c1 = Cascade()
        c1.user1 = u1
        c1.user2 = u2
        c1.user3 = u3
        c1.save()

        a1 = Account()
        a2 = Account()
        a3 = Account()
        c1.accounts.add(a1, a2, a3)
        c1.save()

        # test cascade = None
        c = Cascade.all().fetchone()
        assert c.user3 is not None and c.user3.key == u3.key
        u3.delete()
        c = Cascade.all().fetchone()
        assert c.user3 is None

        # test cascade = False
        try:
            u2.delete()
        except db.IntegrityError:
            c1.user2 = None
            c1.save()
        else:
            self.fail()

        # test cascade = True
        try:
            assert Cascade.all().count() == 1
            u1.delete()
            assert Cascade.all().count() == 0
        except db.IntegrityError:
            self.fail()

    def test_ManyToOne(self):
        u1 = User(name="some")
        u2 = User(name="someone")
        u1.save()
        u2.save()

        a1 = Article(title="story1")
        a2 = Article(title="story2")

        # test direct assignment
        a1.author = u1
        a2.author = u2
        a1.save()
        a2.save()

        assert u1.key == a1.author.key
        assert u2.key == a2.author.key

        # test reverse field
        a3 = Article(title="story3")
        u1.article_set.add(a3)
        u1.save()

        assert u1.key == a3.author.key
        assert u1.article_set.all().count() == 2

        # test type
        try:
            u1.article_set.add(u2)
        except TypeError:
            pass
        else:
            self.fail()

        # get article by author some with title story1
        a = u1.article_set.all().filter('title =', 'story1').fetchone()
        assert a.title == 'story1'
        assert a.author.key == u1.key

    def test_OneToOne(self):
        u1 = User(name="some")
        u2 = User(name="someone")
        u1.save()
        u2.save()

        a1 = Account()
        a2 = Account()

        # check direct assignment
        u1.account = a1
        u1.save()

        assert u1.key == a1.user.key

        # check reverse assignment
        a2.user = u2
        a2.save()

        assert u2.account.key == a2.key

        # check uniqueness
        try:
            u2.account = a1
            u2.save()
        except db.IntegrityError:
            pass
        else:
            self.fail()

    def test_OneToMany(self):
        u1 = User(name="some")
        u1.save()

        a1 = Address(street1="s1")
        a2 = Address(street1="s2")
        a3 = Address(street1="s3")
        a4 = Address(street1="s4")

        # test add
        u1.address_set.add(a1, a2, a3, a4)
        u1.save()

        assert u1.address_set.all().count() == 4
        assert User.all().filter('name =', 'some').fetchone() \
                .address_set.all().count() == 4

        # test clear
        u1.address_set.clear()
        assert u1.address_set.all().count() == 0
        assert User.all().filter('name =', 'some').fetchone() \
                .address_set.all().count() == 0



    def test_ManyToMany(self):
        u1 = User(name="u1")
        u2 = User(name="u2")
        u1.save()
        u2.save()

        g1 = Group(name="g1")
        g2 = Group(name="g2")
        g3 = Group(name="g3")
        g4 = Group(name="g4")

        g1.save()
        g2.save()
        g3.save()
        g4.save()

        # check direct
        g1.members.add(u1, u2)
        g2.members.add(u1)
        assert u1.groups.all().count() == 2
        assert u2.groups.all().count() == 1

        # check reverse
        u1.groups.add(g3, g4)
        assert u1.groups.all().count() == 4
        assert g3.members.all().count() == 1
        assert g4.members.all().count() == 1

    def test_Decimal(self):
        from decimal import Decimal

        obj = FieldType(decimal_value='2.345')
        obj.save()

        assert isinstance(obj.decimal_value, Decimal)
        assert obj.decimal_value == Decimal('2.345')

        obj = FieldType.all().fetchone()

        assert isinstance(obj.decimal_value, Decimal)
        assert obj.decimal_value == Decimal('2.345')

        # validate
        try:
            obj = FieldType(decimal_value=Decimal('2.345'))
        except TypeError:
            self.fail()

        try:
            obj = FieldType(decimal_value=2.345)
        except db.ValidationError:
            pass
        else:
            self.fail()

