from werkzeug import import_string
from werkzeug.contrib.sessions import Session

from rapido.conf import settings
from rapido.web import Middleware


class SessionMiddleware(Middleware):
    
    def __init__(self):
        engine = import_string(
            'rapido.contrib.sessions.engines.%s' % settings.SESSION_ENGINE)
        self.store = engine.Store()
        opts = settings.SESSION_COOKIE
        self.cookie_name = opts.get('name', 'session_id')
        self.cookie_age = opts.get('age', 0)
                
    def process_request(self, request):
        sid = request.cookies.get(self.cookie_name, None)
        request.session = self.store.get(sid) if sid else self.store.new()
        
    def process_response(self, request, response):
        session = request.session
        if session.should_save:
            self.store.save(session)
            response.set_cookie(
                self.cookie_name, session.sid,
                max_age=self.cookie_age)

