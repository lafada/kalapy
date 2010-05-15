import os
from optparse import make_option
from wsgiref import simple_server

from rapido import db
from rapido.admin import BaseCommand

from rapido.web import Application


class RunServer(BaseCommand):

    name = 'runserver'
    args = '[options]'
    help = 'Start the package server.'
    scope = 'package'
    
    options = (
        make_option('-p', '--port', help='Port of the server to run on', 
            default='8080'),
        make_option('-a', '--address', help='Address to which the server should bind.',
            default='localhost'),
        make_option('--no-reload', help='Do not use auto-reload feature.',
            action='store_true', default=False),
    )

    def execute(self, *args, **options):
        host = options.get('host', 'localhost')
        port = int(options.get('port', 8080))
        package = Application()
        server = simple_server.make_server(host, port, package)
        print 'Serving on http://%s:%s' % (host, port)
        server.serve_forever()
