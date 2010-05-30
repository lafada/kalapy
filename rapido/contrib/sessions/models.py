import pickle, base64
from rapido import db

class Session(db.Model):
    sid = db.String(size=50, required=True, unique=True)
    data = db.Text()

    def get_data(self):
        try:
            data = base64.decodestring(self.data)
            return pickle.loads(data)
        except pickle.PickleError:
            return {}

    def set_data(self, data):
        self.data = base64.encodestring(pickle.dumps(data))

