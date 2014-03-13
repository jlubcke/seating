import argparse

from statekeeper import StateKeeper
from evaluators import HillClimber
from server import SeatingMaster
from client import SeatingSlave
from seating import SquareStateEvaluator, start_seating, TablePositionAgnosticClosnessEvaluator


def main(addr='127.0.0.1', port=5000, slave=False):
    if slave:
        client = SeatingSlave(addr, port)
        client.run()
    else:
        state_evaluator = SquareStateEvaluator(TablePositionAgnosticClosnessEvaluator())
        server = SeatingMaster(
            StateKeeper(
                HillClimber(state_evaluator),
                state=start_seating()),
            (addr, 5000),
            state_evaluator
        )
        server.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int)
    parser.add_argument('--addr', type=str)
    parser.add_argument('--slave', action='store_true')
    args = parser.parse_args()
    main(addr=args.addr, port=args.port, slave=args.slave)
