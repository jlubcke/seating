import numpy


class State(object):
    
    def __init__(self, persons=150, meals=5, positions=15, seating=None, geometry=None):

        self.persons = persons
        self.meals = meals
        self.positions = positions

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

    def copy(self):
        return State(persons=self.persons,
                     meals=self.meals,
                     positions=self.positions,
                     seating=self.seating.copy(),
                     geometry=self.geometry.copy())


def closeness(state):
    if state.closeness is not None:
        return state.closeness
    result = numpy.dot(state.seating, state.geometry)
    size = result.shape[0]
    result[numpy.arange(size), numpy.arange(size)] = 0
    state.closeness = result
    return result


def persons_at_each_table(state):
    return state.seating.sum(axis=0)


def swap(state, m, p1, p2):
    i, j = m * state.positions, (m+1) * state.positions
    state.seating[p1, i:j], state.seating[p2, i:j] = state.seating[p2, i:j].copy(), state.seating[p1, i:j].copy()
    state.geometry[i:j, p1], state.geometry[i:j, p2] = state.geometry[i:j, p2].copy(), state.geometry[i:j, p1].copy()
    state.closeness = None


def blind_step(state):
    result = state.copy()
    swap(result, numpy.random.choice(state.meals), numpy.random.choice(state.persons), numpy.random.choice(state.persons))
    return result


def candidate_step(state):
    result = state.copy()
    c = candidates(state)
    swap(result, numpy.random.choice(state.meals), numpy.random.choice(c), numpy.random.choice(state.persons))
    return result


def energy_sum(state):
    n = closeness(state)
    return sum(n[n > 1])


def energy_square(state):
    return energy_sum(state) ** 2


def candidates(state):
    n = closeness(state)
    return numpy.where(n == n.max())[0]


def search(start, step=candidate_step, energy=energy_square, n=10000):
    print "Searching... ",
    state = start

    e = energy(state)
    for t in range(n):
        new_state = step(state)
        new_e = energy(new_state)
        if new_e < e:
            state = new_state
            e = new_e
            print e,
    print "Done"
    return state


def dump(state):
    for m in range(state.meals):
        print "-- %d" % m
        for p in range(state.positions):
            print "   ", (numpy.where(state.seating[:, (m*state.positions + p)] == 1)[0])


def main():
    start = State()
    print start
    dump(start)
    state = search(start)

    print persons_at_each_table(state)
    print state.seating
    dump(state)

    n = closeness(state)
    print n.max()
    print len(numpy.where(n == n.max())[0])

    n = closeness(state)
    n[n == 1] = 0
    print n.sum(axis=0)

if __name__ == '__main__':
    main()
