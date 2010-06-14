from kalapy import db


class Entry(db.Model):
    title = db.String(size=100, required=True)
    pubdate = db.DateTime(default_now=True)
    text = db.Text(required=True)

    @db.validate(text)
    def validate_text(self, value):
        """Validate the blog entry text to meet the norms.
        """
        pass

    @property
    def date(self):
        return self.pubdate.strftime('%Y-%d-%m %H:%M')

