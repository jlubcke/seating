import requests
from seating import State, TablePositionAgnosticClosnessEvaluator, SingleThreadedSearcher, ClosenessStepper, SquareStateEvaluator, PrintLogger


class SeatingSlave(object):
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

    def run(self):
        evaluator = TablePositionAgnosticClosnessEvaluator()
        searcher = SingleThreadedSearcher(
            ClosenessStepper(evaluator),
            SquareStateEvaluator(evaluator),
            PrintLogger()
        )
        while True:
            response = requests.get('http://%s:%s/get_best_state' % (self.addr, self.port))
            state = State.from_json(response.content)
            state, _ = searcher.search(state, n=1000)
            requests.post('http://%s:%s/report_state' % (self.addr, self.port), data=state.to_json())