from kalapy.web import Middleware, Response

class TestMiddleware(Middleware):

    def process_request(self, request):
        if request.path == '/middleware/request':
            return Response('process_request')

    def process_response(self, request, response):
        if request.path == '/middleware/response':
            return Response('process_response')

    def process_exception(self, request, exception):
        if request.path == '/middleware/exception':
            return Response('process_exception')
