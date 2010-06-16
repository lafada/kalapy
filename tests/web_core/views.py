from kalapy import web
from kalapy.web import request

@web.route('/')
def index():
    return request.method

@web.route('/more', methods=('GET',), defaults={'items': 100})
@web.route('/more/<int:items>', methods=('GET', 'POST'))
def more(items):
    return '%s:%s' % (request.method, items)

