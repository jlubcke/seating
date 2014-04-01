from StringIO import StringIO
import random

from bunch import Bunch
import numpy
import simplejson


class State(Bunch):

    def __init__(self, names=None, group_names=None, group_indexes=None, group_weights=None, seating=None, weights=None, fixed=None, geometry=None):
        super(State, self).__init__()
        self.names = names if names is not None else ["Person #%d" % i for i in range(seating.shape[0])]
        self.group_names = group_names if group_names is not None else ["Meal #%d" % i for i in range(len(group_indexes))]
        self.group_indexes = group_indexes
        self.group_weights = group_weights if group_weights else [1] * len(group_indexes)
        self.seating = seating

        if weights is None:
            weights_row = [[weight] * (j - i) for (i, j), weight in zip(self.group_indexes, self.group_weights)]
            weights_row = [w for l in weights_row for w in l]
            weights = numpy.array([weights_row] * seating.shape[0])
        self.weights = weights

        self.fixed = fixed if fixed is not None else numpy.zeros(seating.shape, dtype=bool)
        self.geometry = geometry
        self.closeness = None


    @property
    def persons(self):
        return self.seating.shape[0]

    @staticmethod
    def from_json(json):
        values = simplejson.loads(json)
        return State(names=values['names'],
                     group_names=values['group_names'],
                     group_indexes=values['group_indexes'],
                     group_weights=values['group_weights'],
                     seating=numpy.array(values['seating']),
                     fixed=numpy.array(values['fixed']),
                     weights=numpy.array(values['weights']),
                     geometry=numpy.array(values['geometry']))

    def to_json(self):
        return simplejson.dumps({
            "names": self.names,
            "group_names": self.group_names,
            "group_indexes": self.group_indexes,
            "group_weights": self.group_weights,
            "seating": self.seating.tolist(),
            "weights": self.weights.tolist(),
            "fixed": self.fixed.tolist(),
            "geometry": self.geometry.tolist()
        })

    def copy(self):
        return State(names=self.names,
                     group_names=self.group_names,
                     group_indexes=self.group_indexes,
                     group_weights=self.group_weights,
                     seating=self.seating.copy(),
                     fixed=self.fixed,
                     weights=self.weights,
                     geometry=self.geometry.copy())

    def swap(self, i, j, p1, p2):
        p1_seating = self.seating[p1, i:j]
        p2_seating = self.seating[p2, i:j]

        p1_not_here = not numpy.any(p1_seating)
        if p1_not_here:
            return False
        p2_not_here = not numpy.any(p2_seating)
        if p2_not_here:
            return False
        p1_locked = numpy.any(p1_seating * self.fixed[p1, i:j])
        if p1_locked:
            return False
        p2_locked = numpy.any(p2_seating * self.fixed[p2, i:j])
        if p2_locked:
            return False
        self.seating[p1, i:j], self.seating[p2, i:j] = p2_seating.copy(), p1_seating.copy()
        self.geometry[i:j, p1], self.geometry[i:j, p2] = self.geometry[i:j, p2].copy(), self.geometry[i:j, p1].copy()
        self.closeness = None
        return True

    def shuffle(self):
        for i, j in self.group_indexes:
            if i + 1 == j:
                continue
            for p1 in range(self.persons):
                p2 = numpy.random.choice(self.persons)
                if self.swap(i, j, p1, p2):
                    self.seating = self.seating.copy()
                    self.geometry = self.geometry.copy()


def start_seating(persons=150, meals=5, groups=10, positions=15):

    names = ["Person #%03d" % i for i in range(persons)]
    group_names = ["Meal #%d" % i for i in range(meals)]
    group_names.extend(["Group #%d" % i for i in range(groups)])

    seating = numpy.zeros((persons, meals * positions + groups), dtype=int)

    group_indexes = [[i*positions, (i+1)*positions] for i in range(meals)]
    group_weights = [1] * len(group_indexes)
    group_indexes += [[i, i+1] for i in range(meals*positions, meals*positions + groups)]
    group_weights += range(2, 2 + groups)

    # Some random groups
    seating[:, meals*positions:(meals*positions + groups)] = numpy.random.random_integers(0, 1, size=(persons, groups))
    seating[0, meals*positions:(meals*positions + groups)] = numpy.ones(shape=(1, groups))  # Avoid empty groups...

    # Naive initial seating
    for m, (i, j) in enumerate(group_indexes[:meals]):
        persons_per_table = persons / (j - i)
        for p in range(persons):
            seating[p, i + p / persons_per_table] = 1

    geometry = seating.copy().transpose()

    return State(names=names,
                 group_names=group_names,
                 group_indexes=group_indexes,
                 group_weights=group_weights,
                 seating=seating,
                 geometry=geometry)


class Stepper(object):
    def step(self, state):
        raise NotImplementedError


class BlindStepper(Stepper):
    def step(self, state):
        result = state.copy()
        while True:
            i, j = random.choice(state.group_indexes)
            if i + 1 == j:
                continue
            if result.swap(i, j,
                           numpy.random.choice(state.persons),
                           numpy.random.choice(state.persons)):
                return result


class ClosenessStepper(Stepper):
    def __init__(self, closeness_evaluator):
        self.closeness_evaluator = closeness_evaluator

    def step(self, state):
        result = state.copy()
        c = self._candidates(state)
        while True:
            i, j = random.choice(state.group_indexes)
            if i + 1 == j:
                continue
            if result.swap(i, j,
                           numpy.random.choice(c),
                           numpy.random.choice(state.persons)):
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
        result = numpy.dot(state.seating * state.weights, state.geometry)
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
                self.log("New best state energy: " + str(e))
        self.log("Done")
        return state, e


def dump(state):
    result = StringIO()
    for m, (i, j) in enumerate(state.group_indexes):
        result.write("-- %s\n" % state.group_names[m])
        for p in range(i, j):
            result.write("   %s\n" % (numpy.where(state.seating[:, p] == 1)[0]))
    return result.getvalue()


def report(state):

    result = StringIO()

    attendance = numpy.dot(state.seating.transpose(), state.seating)

    for group_name, (i, j) in zip(state.group_names, state.group_indexes):
        if i + 1 == j:
            continue
        result.write("%s\n" % group_name)

        cnt = 0
        for table in range(i, j):
            result.write("  %s\n" % cnt)

            for inner_group_name, (k, l) in zip(state.group_names, state.group_indexes):
                if k + 1 != l:
                    continue
                n = attendance[i+cnt][k]
                if n > 0:
                    result.write("    %s: %d\n" % (inner_group_name, n))
            cnt += 1

    return result.getvalue()


class PrintLogger(object):
    def __init__(self):
        pass

    def log(self, msg):
        print msg


def optimize(start):
    start.shuffle()
    evaluator = TablePositionAgnosticClosnessEvaluator()
    searcher = SingleThreadedSearcher(
        ClosenessStepper(evaluator),
        SquareStateEvaluator(evaluator),
        PrintLogger()
    )
    state, _ = searcher.search(start)
    return state


def main():
    start = start_seating()
    print start.seating
    print dump(start)
    start.shuffle()
    print dump(start)

    evaluator = TablePositionAgnosticClosnessEvaluator()
    searcher = SingleThreadedSearcher(
        ClosenessStepper(evaluator),
        SquareStateEvaluator(evaluator),
        PrintLogger()
    )
    state, _ = searcher.search(start)

    print persons_at_each_table(state)
    print state.seating
    print dump(state)

    n = evaluator.closeness(state)
    print n.max()
    print len(numpy.where(n == n.max())[0])

    n = evaluator.closeness(state)
    n[n == 1] = 0
    print n.sum(axis=0)

    print dump(state)
    print report(state)


if __name__ == '__main__':
    main()
