from rapido import db


class User(db.Model):
    name = db.String(size=100, required=True)
    lang = db.String(size=6, selection=[('en_EN', 'English'),
                                        ('fr_FR', 'French'),
                                        ('de_DE', 'German')])

    def do_something(self):
        return 1

class UserDOB(User):
    dob = db.Date()

    def do_something(self):
        return super(UserDOB, self).do_something() + 1

class UserNotes(UserDOB):
    notes = db.Text()

    def do_something(self):
        return super(UserNotes, self).do_something() + 1

class UserAccount(User):
    account = db.OneToOne('Account', reverse_name='user')

    def do_something(self):
        return super(UserAccount, self).do_something() + 1

class Address(db.Model):
    street1 = db.String(size=100, required=True)
    street1 = db.String(size=100)
    city = db.String(size=100)
    zip = db.String(size=100)
    user = db.ManyToOne(User)

class Group(db.Model):
    name = db.String(size=50, required=True, unique=True)
    parent = db.ManyToOne('Group', reverse_name='subgroups')
    members = db.ManyToMany(User, reverse_name='groups')

class Account(db.Model):
    create_date = db.DateTime(default_now=True)
    expire_date = db.DateTime()

class Article(db.Model):
    title = db.String(size=100, required=True)
    pub_date = db.DateTime(default_now=True)
    text = db.Text()
    author = db.ManyToOne(User)

class Comment(db.Model):
    title = db.String(size=100, required=True)
    pub_date = db.DateTime(default_now=True)
    text = db.Text()
    article = db.ManyToOne(Article)
    author = db.ManyToOne(User)
    parent = db.ManyToOne('Comment', reverse_name='children')

class UniqueTest(db.Model):
    a = db.String()
    b = db.String()
    c = db.String()

    db.unique(a, [b, c])

    @db.validate(a)
    def chk_a(self, value):
        if len(value) < 3:
            raise db.ValidationError('Too short value')

