from kalapy import db

class Foo(db.Model):
    name = db.String(size=100)
