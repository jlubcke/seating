from abc import ABCMeta, abstractmethod


class StateEvaluator(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def challenge(self):
        pass


class StateKeeper(object):
    def __init__(self, challenge_evaluator):
        self._current_state = None
        assert issubclass(type(challenge_evaluator), StateEvaluator)
        self.challenge_evaluator = challenge_evaluator

    def get_current_state(self):
        return self._current_state

    def challenge_state(self, state):
        prev_state = self._current_state
        if self._current_state is None:
            self._current_state = state
        else:
            self._current_state = self.challenge_evaluator.challenge(self._current_state, state)
        return prev_state != self._current_state

