from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from excel_format import write_excel
from seating import State, dump, report
from text_format import write_text


class SeatingMaster(object):

    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            response = self.server.dispatcher('GET', self.path, None)
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(response.encode('utf8') if response is not None else '')

        def do_POST(self):
            data = self.rfile.read(int(self.headers.getheader('Content-Length')))
            response = self.server.dispatcher('POST', self.path, data)
            self.send_response(200)
            self.send_header("content-type", "text/plain")
            self.end_headers()
            self.wfile.write(response.encode('utf8') if response is not None else '')

    class SeatingServer(HTTPServer):
        def __init__(self, dispatcher, *args, **kwargs):
            self.dispatcher = dispatcher
            HTTPServer.__init__(self, *args, **kwargs)

    def __init__(self, state_keeper, server_address, state_evaluator):
        def dispatcher(method, path, data):
            if method == 'GET' and path == '/get_best_state':
                return self.get_best_state()
            if method == 'GET' and path =='/dump':
                return self.dump()
            if method == 'GET' and path =='/export':
                return self.export()
            if method == 'GET' and path == '/excel':
                return self.excel()
            if method == 'POST' and path == '/report_state':
                return self.report_state(data)

        self.state_evaluator = state_evaluator

        self._server = SeatingMaster.SeatingServer(dispatcher, server_address, SeatingMaster.RequestHandler)
        self.state_keeper = state_keeper
        self.keep_running = False

    def dump(self):
        state = self.state_keeper.get_current_state()
        return dump(state) + u"\n%s\n" % (u"#"*80,) + report(state)

    def export(self):
        return write_text(self.state_keeper.get_current_state())

    def excel(self):
        return write_excel(self.state_keeper.get_current_state())

    def get_best_state(self):
        state = self.state_keeper.get_current_state()
        if state is not None:
            return state.to_json()
        else:
            return 'None'

    def report_state(self, data):
        state = State.from_json(data)
        if self.state_keeper.challenge_state(state):
            print "Energy of current state:", self.state_evaluator.evaluate(state)
            return 'Accepted'
        else:
            return 'Discarded'

    def run(self):
        self.keep_running = True
        while self.keep_running:
            self._server.handle_request()
