import numpy
import random


class State(object):

    def __init__(self, meal_indexes=None, seating=None, geometry=None):

        self.meal_indexes = meal_indexes
        self.seating = seating
        self.geometry = geometry
        self.closeness = None

    @property
    def persons(self):
        return self.seating.shape[0]

    def copy(self):
        return State(meal_indexes=self.meal_indexes,
                     seating=self.seating.copy(),
                     geometry=self.geometry.copy())

    def swap(self, i, j, p1, p2):
        if not self.seating[p1, i:j].any() or not self.seating[p2, i:j].any():
            return
        self.seating[p1, i:j], self.seating[p2, i:j] = self.seating[p2, i:j].copy(), self.seating[p1, i:j].copy()
        self.geometry[i:j, p1], self.geometry[i:j, p2] = self.geometry[i:j, p2].copy(), self.geometry[i:j, p1].copy()
        self.closeness = None


def start_seating(persons=150, meals=5, groups=10, positions=15):

    state = State()

    state.seating = numpy.zeros((persons, meals * positions + groups), dtype=int)

    state.meal_indexes = [(i*positions, (i+1)*positions) for i in range(meals)]

    # Some random groups
    state.seating[:, meals*positions:(meals*positions + groups)] = numpy.random.random_integers(0, 1, size=(persons, groups))

    # Naive initial seating
    for m, (i, j) in enumerate(state.meal_indexes):
        persons_per_table = persons / (j - i)
        t1 = range(0, persons/2)
        t2 = range(persons/2, persons)
        if m == 0:
            persons_at_meal = t1
        elif m == meals - 1:
            persons_at_meal = t2
        else:
            persons_at_meal = t1 + t2
        for k, p in enumerate(persons_at_meal):
            state.seating[p, i + k / persons_per_table] = 1

    state.geometry = state.seating.transpose()

    return state


class Stepper(object):
    def step(self, state):
        raise NotImplementedError


class BlindStepper(Stepper):
    def step(self, state):
        result = state.copy()
        i, j = random.choice(state.meal_indexes)
        result.swap(i, j,
                    numpy.random.choice(state.persons),
                    numpy.random.choice(state.persons))
        return result


class ClosenessStepper(Stepper):

    def __init__(self, closeness_evaluator):
        self.closeness_evaluator = closeness_evaluator

    def step(self, state):
        result = state.copy()
        c = self._candidates(state)
        i, j = random.choice(state.meal_indexes)
        result.swap(i, j,
                    numpy.random.choice(c),
                    numpy.random.choice(state.persons))
        return result

    def _candidates(self, state):
        n = self.closeness_evaluator.closeness(state)
        return numpy.where(n == n.max())[0]


class ClosenessEvaluator(object):
    def closeness(self, state):
        raise NotImplementedError


class TablePositionAgnosticClosnessEvaluator(ClosenessEvaluator):

    def closeness(self, state):
        if state.closeness is not None:
            return state.closeness
        result = numpy.dot(state.seating, state.geometry)
        size = result.shape[0]
        result[numpy.arange(size), numpy.arange(size)] = 0
        state.closeness = result
        return result


class StateEvaluator(object):
    def evaluate(self, state):
        pass


class SquareStateEvaluator(StateEvaluator):
    def __init__(self, closeness_evaluator):
        self.closeness_evaluator = closeness_evaluator

    def evaluate(self, state):
        return self._energy_sum(state) ** 2

    def _energy_sum(self, state):
        n = self.closeness_evaluator.closeness(state)
        return sum(n[n > 1])


def persons_at_each_table(state):
    return state.seating.sum(axis=0)


class Searcher(object):
    def search(self, start, iterations):
        pass


class SingleThreadedSearcher(Searcher):

    def __init__(self, stepper, state_evaluator, logger):
        self.stepper = stepper
        self.state_evaluator = state_evaluator
        self.logger = logger

    def log(self, msg):
        self.logger.log(msg)

    def search(self, start, n=10000):
        self.log("Searching... ")
        state = start

        e = self.state_evaluator.evaluate(state)
        for t in range(n):
            new_state = self.stepper.step(state)
            new_e = self.state_evaluator.evaluate(new_state)
            if new_e < e:
                state = new_state
                e = new_e
                self.log("New best energy: " + str(e))
        self.log("Done")
        return state, e


def dump(state):
    for m, (i, j) in enumerate(state.meal_indexes):
        print "-- %d" % m
        for p in range(i, j):
            print "   ", (numpy.where(state.seating[:, p] == 1)[0])


class PrintLogger(object):
    def __init__(self):
        pass

    def log(self, msg):
        print msg


def main():
    start = start_seating()
    print start.seating
    dump(start)
    evaluator = TablePositionAgnosticClosnessEvaluator()
    searcher = SingleThreadedSearcher(
        ClosenessStepper(evaluator),
        SquareStateEvaluator(evaluator),
        PrintLogger()
    )
    state, _ = searcher.search(start)

    print persons_at_each_table(state)
    print state.seating
    dump(state)

    n = evaluator.closeness(state)
    print n.max()
    print len(numpy.where(n == n.max())[0])

    n = evaluator.closeness(state)
    n[n == 1] = 0
    print n.sum(axis=0)

if __name__ == '__main__':
    main()
