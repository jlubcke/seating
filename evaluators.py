from statekeeper import StateEvaluator


class HillClimber(StateEvaluator):

    def __init__(self, state_evaluator):
        self.state_evaluator = state_evaluator

    def challenge(self, state1, state2):
        return state1 if self.state_evaluator.evaluate(state2) > self.state_evaluator.evaluate(state1) else state2
