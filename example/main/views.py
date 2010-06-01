from rapido import web

@web.route('/')
def index():
    return web.render_template('index.html')

