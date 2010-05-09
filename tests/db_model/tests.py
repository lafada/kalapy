from rapido.db.engines import database
from rapido.test import TestCase

from models import *


class BaseTest(TestCase):

    def setUp(self):
        super(BaseTest, self).setUp()
        for model in db.get_models():
            database.create_table(model)

    def tearDown(self):
        super(BaseTest, self).tearDown()


class ModelTest(BaseTest):

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
        
        u1 = User(name="some")
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
        u1 = User(name="some")
        key = u1.save()
        u1.delete()

        u2 = User.get(key)

        self.assertTrue(u2 is None)

    def test_model_get(self):
        u1 = User(name="some1")
        u2 = User(name="some2")
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
        u1 = User(name="some1")
        u1.save() # ensure at least one record exists
        
        res = User.all().filter('name == :name', name=u1.name).fetch(-1)
        self.assertTrue(len(res) > 0)

    def test_model_select(self):
        u1 = User(name="some1")
        u1.save() # ensure at least one record exists
        
        names = User.select('name').filter('name == :name', name=u1.name).fetch(-1)
        self.assertTrue(names[0] == u1.name)


class FieldTest(BaseTest):

    def setUp(self):
        super(FieldTest, self).setUp()
        self.user = User(name="some", dob='1996-11-04')
        self.user.save()

    def tearDown(self):
        super(FieldTest, self).tearDown()
        self.user.delete()

    def test_field_required(self):
        try:
            self.user.name = None
        except db.ValidationError:
            pass
        else:
            self.fail()

    def test_field_unique(self):
        
        u = UniqueTest(a='aaab', b='b', c='c')
        u.save()

        u2 = UniqueTest(a='aaaa', b='b', c='d')
        u3 = UniqueTest(a='bbbb', b='b', c='c')

        try:
            u2.save()
            u3.save()
        except db.IntegrityError:
            pass
        else:
            self.fail()
        finally:
            u.delete()

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
        u.a = 'aaaaa'
        try:
            u.a = 'aa'
        except db.ValidationError:
            pass
        else:
            self.fail()

