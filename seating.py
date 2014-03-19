from StringIO import StringIO
import random
import sys
from io import BytesIO

import numpy
import simplejson


class State(object):

    def __init__(self, names=None, group_names=None, group_indexes=None, seating=None, fixed=None, geometry=None):

        self.names = names if names is not None else ["Person #%d" % i for i in range(seating.shape[0])]
        self.group_names = group_names if group_names is not None else ["Meal #%d" % i for i in range(len(group_indexes))]
        self.group_indexes = group_indexes
        self.seating = seating
        self.fixed = fixed if fixed is not None else numpy.zeros(seating.shape, dtype=bool)
        self.geometry = geometry
        self.closeness = None


    @property
    def persons(self):
        return self.seating.shape[0]

    @staticmethod
    def from_json(json):
        state_as_dict = simplejson.loads(json)
        return State(group_names=state_as_dict['group_names'],
                     group_indexes=state_as_dict['group_indexes'],
                     seating=numpy.array(state_as_dict['seating']),
                     fixed=numpy.array(state_as_dict['fixed']),
                     geometry=numpy.array(state_as_dict['geometry']))

    def to_json(self):
        return simplejson.dumps({
            "group_names": self.group_names,
            "gropu_indexes": self.group_indexes,
            "seating": self.seating.tolist(),
            "fixed": self.fixed.tolist(),
            "geometry": self.geometry.tolist()
        })

    def copy(self):
        return State(names=self.names,
                     group_names=self.group_names,
                     group_indexes=self.group_indexes,
                     seating=self.seating.copy(),
                     fixed=self.fixed,
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

    names = ["Person #%d" % i for i in range(persons)]
    group_names = ["Meal #%d" % i for i in range(meals)]
    group_names.extend(["Group #%d" % i for i in range(groups)])

    seating = numpy.zeros((persons, meals * positions + groups), dtype=int)

    group_indexes = [(i*positions, (i+1)*positions) for i in range(meals)]
    group_indexes += [(i, i+1) for i in range(meals*positions, meals*positions + groups)]

    # Some random groups
    seating[:, meals*positions:(meals*positions + groups)] = numpy.random.random_integers(0, 1, size=(persons, groups))

    # Naive initial seating
    for m, (i, j) in enumerate(group_indexes[:meals]):
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
            seating[p, i + k / persons_per_table] = 1

    geometry = seating.copy().transpose()

    return State(names=names,
                 group_names=group_names,
                 group_indexes=group_indexes,
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

            for group_name, (k, l) in zip(state.group_names, state.group_indexes):
                if k + 1 != l:
                    continue
                n = attendance[i+cnt][k]
                if n > 0:
                    result.write("    %s: %d\n" % (group_name, n))
            cnt += 1

    return result.getvalue()


class PrintLogger(object):
    def __init__(self):
        pass

    def log(self, msg):
        print msg


def parse(filename):

    group_names = []
    groups = []

    group = []
    position = []

    with open(filename, "rb") as f:
        for line in f:
            if line.startswith('#'):
                group_names.append(line[1:].strip())
                if position:
                    group.append(position)
                    position = []
                if group:
                    groups.append(group)
                    group = []
            elif line.strip() == '':
                if position:
                    group.append(position)
                    position = []
            else:
                fixed = line.startswith('*')
                if fixed:
                    line = line[1:]
                position.append([line.strip(), fixed])

        if position:
            group.append(position)
        if group:
            groups.append(group)

    cnt = 0
    group_indexes = []
    for group in groups:
        group_indexes.append((cnt, cnt + len(group)))
        cnt += len(group)

    names = list({name
                  for group in groups
                  for position in group
                  for (name, _) in position})
    names.sort()

    group_indexes = group_indexes

    seating = numpy.zeros((len(names), group_indexes[-1][1]), dtype=int)
    fixed = numpy.zeros((len(names), group_indexes[-1][1]), dtype=bool)

    persons_by_name = {name: idx for idx, name in enumerate(names)}
    cnt = 0
    for group in groups:
        for position in group:
            for name, is_fixed in position:
                row = persons_by_name[name]
                seating[row, cnt] = 1
                fixed[row, cnt] = is_fixed
            cnt += 1

    geometry = seating.copy().transpose()

    return State(names=names,
                 group_names=group_names,
                 group_indexes=group_indexes,
                 seating=seating,
                 fixed=fixed,
                 geometry=geometry)


def export(state):
    result = StringIO()

    for group_name, (i, j) in zip(state.group_names, state.group_indexes):
        result.write('# ' + group_name + "\n\n")
        for t in range(i, j):
            for p in numpy.where(state.seating[:, t] == 1)[0]:
                if state.fixed[p, t]:
                    result.write('*')
                result.write(state.names[p] + '\n')
            result.write('\n')
        result.write('\n')
    return result.getvalue()


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
    if len(sys.argv) == 2:
        start = parse(sys.argv[1])
    else:
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

    print export(state)


if __name__ == '__main__':
    main()
