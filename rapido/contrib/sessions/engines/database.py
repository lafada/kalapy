import pickle
from werkzeug.contrib.sessions import SessionStore

from rapido import db
from ..models import Session


class Store(SessionStore):

    def __init__(self, session_class=None):
        super(Store, self).__init__(session_class)

    def get_session(self, sid):
        obj = Session.all().filter('sid == :sid', sid=sid).fetch(1)
        return obj[0] if obj else None

    def save(self, session):
        obj = self.get_session(session.sid) or Session(sid=session.sid)
        try:
            obj.set_data(dict(session))
            obj.save()
            db.commit()
        except pickle.PickleError:
            pass

    def delete(self, session):
        obj = self.get_session(session.sid)
        if obj:
            obj.delete()
            db.commit()

    def get(self, sid):
        if not self.is_valid_key(sid):
            return self.session_class.new()
        obj = self.get_session(sid)
        try:
            data = obj.get_data()
        except:
            data = {}
        return self.session_class(data, sid, False)

    def list(self):
        return Session.select('sid').fetch(-1)
