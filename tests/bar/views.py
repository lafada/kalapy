from kalapy import web

from kalapy import web

@web.route('/')
def index():
    return 'bar:index'

@web.route('/bar')
def bar():
    return web.render_template('bar.html')


