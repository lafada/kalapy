from kalapy.test import TestCase


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

