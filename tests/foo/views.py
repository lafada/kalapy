from kalapy import web

@web.route('/')
def index():
    return 'foo:index'

@web.route('/foo')
def foo():
    return web.render_template('foo.html')

