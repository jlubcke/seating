import numpy


class State(object):
    
    def __init__(self, persons=150, meals=5, positions=15, seating=None, geometry=None):

        self.persons = persons
        self.meals = meals
        self.positions = positions
        self.energy = None

        if seating is not None:
            self.seating = seating
            self.geometry = geometry
        else:
            self.set_start_seating()

        self.closeness = None

    def set_start_seating(self):
        self.seating = numpy.zeros((self.persons, self.meals * self.positions), dtype=int)
        persons_per_table = self.persons / self.positions
        for m in range(self.meals):
            first_table_index = m * self.positions
            for t in range(self.persons):
                self.seating[t, first_table_index + t / persons_per_table] = 1
        self.geometry = self.seating.transpose()

    def swap(self, m, p1, p2):
        i, j = m * self.positions, (m+1) * self.positions
        self.seating[p1, i:j], self.seating[p2, i:j] = self.seating[p2, i:j].copy(), self.seating[p1, i:j].copy()
        self.geometry[i:j, p1], self.geometry[i:j, p2] = self.geometry[i:j, p2].copy(), self.geometry[i:j, p1].copy()
        self.closeness = None

    def copy(self):
        return State(persons=self.persons,
                     meals=self.meals,
                     positions=self.positions,
                     seating=self.seating.copy(),
                     geometry=self.geometry.copy())


class Stepper(object):
    def step(self, state):
        raise NotImplementedError


class BlindStepper(Stepper):
    def step(self, state):
        result = state.copy()
        result.swap(numpy.random.choice(state.meals),
                    numpy.random.choice(state.persons),
                    numpy.random.choice(state.persons))
        return result


class ClosenessStepper(Stepper):

    def __init__(self, closeness_evaluator):
        self.closeness_evaluator = closeness_evaluator

    def step(self, state):
        result = state.copy()
        c = self._candidates(state)
        result.swap(numpy.random.choice(state.meals),
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
    for m in range(state.meals):
        print "-- %d" % m
        for p in range(state.positions):
            print "   ", (numpy.where(state.seating[:, (m*state.positions + p)] == 1)[0])


class PrintLogger(object):
    def __init__(self):
        pass

    def log(self, msg):
        print msg


def main():
    start = State()
    print start
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
