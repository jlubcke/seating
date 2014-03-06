from statekeeper import StateEvaluator


class HillClimber(StateEvaluator):
    def challenge(self, state1, state2):
        return state1 if state2.energy > state1.energy else state2
