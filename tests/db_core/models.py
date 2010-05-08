from rapido import db

class Article(db.Model):
    title = db.String(size=100, required=True)
    pub_date = db.DateTime(default_now=True)
    text = db.Text()

