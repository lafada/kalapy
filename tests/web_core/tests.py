# -*- coding: utf-8 -*-
from kalapy import web
from kalapy.conf import settings
from kalapy.test import TestCase

try:
    import simplejson as json
except:
    import json


class CoreTest(TestCase):

    def test_request_dispatching(self):
        c = self.client
        rv = c.get('/')
        assert rv.data == 'GET'
        rv = c.post('/')
        assert rv.status_code == 405
        assert sorted(rv.allow) == ['GET', 'HEAD']
        rv = c.head('/')
        assert rv.status_code == 200
        assert not rv.data  # head truncates
        assert c.get('/more').data == 'GET:100'
        rv = c.post('/more')
        assert rv.status_code == 405
        assert sorted(rv.allow) == ['GET', 'HEAD']
        assert c.get('/more/200').data == 'GET:200'
        assert c.post('/more/200').data == 'POST:200'
        rv = c.delete('/more/200')
        assert rv.status_code == 405
        assert sorted(rv.allow) == ['GET', 'HEAD', 'POST']

    def test_response_creation(self):
        c = self.client
        assert c.get('/response/unicode').data == u'Hällo Wörld'.encode('utf-8')
        assert c.get('/response/str').data == u'Hällo Wörld'.encode('utf-8')
        rv = c.get('/response/tuple')
        assert rv.data == 'Meh'
        assert rv.headers['X-Foo'] == 'Testing'
        assert rv.status_code == 400
        assert rv.mimetype == 'text/plain'
        rv = c.get('/response/dict')
        assert rv.data == '{"json": true}'
        assert rv.mimetype == 'application/json'
        try:
            rv = c.get('/response/None')
        except ValueError, e:
            str(e) == 'View function should return a response'
            pass
        else:
            assert 'Expected ValueError'

    def test_url_generation(self):
        assert web.url_for('response', kind="no thing", extra='test x') \
            == '/response/no%20thing?extra=test+x'
        assert web.url_for('response', kind="no thing", extra='test x', _external=True) \
            == 'http://%s/response/no%%20thing?extra=test+x' % settings.SERVERNAME

    def test_static_files(self):
        static_file = web.url_for('static', filename='index.html')
        assert static_file == '/web_core/static/index.html'
        rv = self.client.get(static_file)
        assert rv.status_code == 200
        assert rv.data.strip() == '<h1>Hello World!</h1>'


class JSONTest(TestCase):

    def test_jsonify(self):
        rv = self.client.get('/json1')
        assert rv.mimetype == 'application/json'
        json.loads(rv.data) == dict(a=1, b=2, c=[3, 4, 5])
        rv = self.client.get('/json2')
        assert rv.mimetype == 'application/json'
        json.loads(rv.data) == dict(a=1, b=2, c=[3, 4, 5])


class TemplateTest(TestCase):

    def test_template(self):
        rv = self.client.get('/template/1/2/3/4')
        assert rv.data == '<p>1/2/3/4</p>'


class MiddlewareTest(TestCase):

    def test_process_request(self):
        rv = self.client.get('/middleware/request')
        assert rv.data == 'process_request'
        rv = self.client.get('/middleware/response')
        assert rv.data == 'process_response'
        rv = self.client.get('/middleware/exception')
        assert rv.data == 'process_exception'


