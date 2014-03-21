import argparse

from excel_format import read_excel
from statekeeper import StateKeeper
from evaluators import HillClimber
from server import SeatingMaster
from client import SeatingSlave
from seating import SquareStateEvaluator, start_seating, TablePositionAgnosticClosnessEvaluator
from text_format import read_text


def main(start=None, addr=None, port=None, slave=None):
    if slave:
        client = SeatingSlave(addr, port)
        client.run()
    else:

        if start.endswith('.xls') or start.endswith('.xlsx'):
            state = read_excel(start)
        elif start.endswith('.txt'):
            state = read_text(start)
        else:
            state = None

        if state is None:
            state = start_seating()

        state.shuffle()

        state_evaluator = SquareStateEvaluator(TablePositionAgnosticClosnessEvaluator())
        server = SeatingMaster(
            StateKeeper(
                HillClimber(state_evaluator),
                state=state),
            (addr, 5000),
            state_evaluator
        )
        server.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=str)
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--addr', type=str, default="127.0.0.1")
    parser.add_argument('--slave', action='store_true')
    args = parser.parse_args()
    main(addr=args.addr, port=args.port, slave=args.slave, start=args.start)
