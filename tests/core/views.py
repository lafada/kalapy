# -*- coding: utf-8 -*-
from kalapy import web
from kalapy.web import request

@web.route('/')
def index():
    return request.method

@web.route('/more', methods=('GET',), defaults={'items': 100})
@web.route('/more/<int:items>', methods=('GET', 'POST'))
def more(items):
    return '%s:%s' % (request.method, items)

@web.route('/response/<kind>')
def response(kind):
    if kind == 'unicode':
        return u'Hällo Wörld'
    if kind == 'str':
        return u'Hällo Wörld'.encode('utf-8')
    if kind == 'tuple':
        return 'Meh', 400, {'X-Foo': 'Testing'}, 'text/plain'
    if kind == 'dict':
        return dict(json=True)
    if kind == 'None':
        return None
    return 'Hello World'

@web.route('/json1')
def json1():
    return web.jsonify(dict(a=1, b=2, c=[3, 4, 5]))

@web.route('/json2')
def json2():
    return web.jsonify(a=1, b=2, c=[3, 4, 5])

@web.route('/template/<path:args>')
def template(args):
    return web.render_template('test_template.html', args=args)

@web.route('/middleware/<action>')
def middleware(action):
    if action == 'exception':
        1/0
    return action

