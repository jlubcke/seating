from searchresult import SearchResult
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


class SeatingMaster(object):

    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            response = self.server.dispatcher('GET', self.path, None)
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(response)

        def do_POST(self):
            data = self.rfile.read(int(self.headers.getheader('Content-Length')))
            response = self.server.dispatcher('POST', self.path, data)
            self.send_response(200)
            self.send_header("content-type", "text/plain")
            self.end_headers()
            self.wfile.write(response)

    class SeatingServer(HTTPServer):
        def __init__(self, dispatcher, *args, **kwargs):
            self.dispatcher = dispatcher
            HTTPServer.__init__(self, *args, **kwargs)

    def __init__(self, state_keeper, server_address):
        def dispatcher(method, path, data):
            if method == 'GET' and path == '/get_best_state':
                return self.get_best_state()
            if method == 'POST' and path == '/report_state':
                return self.report_state(data)

        self._server = SeatingMaster.SeatingServer(dispatcher, server_address, SeatingMaster.RequestHandler)
        self.state_keeper = state_keeper
        self.keep_running = False

    def get_best_state(self):
        state = self.state_keeper.get_current_state()
        if state is not None:
            return state.to_json()
        else:
            return 'None'

    def report_state(self, data):
        if self.state_keeper.challenge_state(SearchResult.from_json(data)):
            return 'Accepted'
        else:
            return 'Discarded'

    def run(self):
        self.keep_running = True
        while self.keep_running:
            self._server.handle_request()