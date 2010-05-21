import os
from optparse import make_option

from rapido.admin import BaseCommand
from rapido.web import simple_server


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
        host = options.get('host', '127.0.0.1')
        port = int(options.get('port', 8080))
        use_reloader = not options.get('no_reload', True)
        simple_server(host, port, use_reloader)

