import numpy

class State(object):
    
    def __init__(self, persons=150, meals=5, positions=15, seating=None):

        self.persons = persons
        self.meals = meals
        self.positions = positions

        if seating is not None:
            self.seating = seating
        else:
            self.set_start_seating()

    def set_start_seating(self):
        self.seating = numpy.zeros((self.persons, self.meals * self.positions), dtype=int)
        persons_per_table = self.persons / self.positions
        for m in range(self.meals):
            first_table_index = m * self.positions
            for t in range(self.persons):
                self.seating[t, first_table_index + t / persons_per_table] = 1

    def copy(self):
        return State(persons=self.persons,
                     meals=self.meals,
                     positions=self.positions,
                     seating=self.seating.copy())


def neighbourness_old(state):

    result = numpy.zeros((state.persons, state.persons))

    for p1 in range(state.persons):
        for p2 in range(state.persons):
            if p1 != p2:
                result[p1, p2] = sum(state.seating[p1, :] * state.seating[p2, :])

    return result


def neighbourness(state):
    result = numpy.dot(state.seating, state.seating.transpose())
    size = result.shape[0]
    result[numpy.arange(size), numpy.arange(size)] = 0
    return result


def persons_at_each_table(state):
    return state.seating.sum(axis=0)


def swap(state, m, p1, p2):
    i, j = m * state.positions, (m+1) * state.positions
    state.seating[p1, i:j], state.seating[p2, i:j] = state.seating[p2, i:j].copy(), state.seating[p1, i:j].copy()


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
    n = neighbourness(state)
    return sum(n[n > 1])


def energy_square(state):
    return energy_sum(state) ** 2


def candidates(state):
    n = neighbourness(state)
    return numpy.where(n == n.max())[0]


def search(start, step=blind_step, energy=energy_sum, n=10000):
    print "Searching... ",
    state = start

    e = energy(state)
    for t in range(n):
        candidate = step(state)
        new_e = energy(candidate)
        if new_e < e:
            state = candidate
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

    n = neighbourness(state)
    print n.max()
    print len(numpy.where(n == n.max())[0])

    n = neighbourness(state)
    n[n == 1] = 0
    print n.sum(axis=0)

if __name__ == '__main__':
    main()
