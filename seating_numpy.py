import numpy

PERSONS = 150
MEALS = 5
POSITIONS = 15


def initial():
    seating = numpy.zeros((PERSONS, MEALS * POSITIONS), dtype=int)
    persons_per_table = PERSONS / POSITIONS
    for m in range(MEALS):
        first_table_index = m * POSITIONS
        for t in range(PERSONS):
            seating[t, first_table_index + t / persons_per_table] = 1
    return seating


def neighbourness_old(seating):
    result = numpy.zeros((PERSONS, PERSONS))

    for p1 in range(PERSONS):
        for p2 in range(PERSONS):
            if p1 != p2:
                result[p1, p2] = sum(seating[p1, :] * seating[p2, :])

    return result


def neighbourness(seating):
    result = numpy.dot(seating, seating.transpose())
    size = result.shape[0]
    result[numpy.arange(size), numpy.arange(size)] = 0
    return result


def persons_at_each_table(seating):
    result = numpy.zeros(seating.shape[1])
    for t in range(seating.shape[1]):
        result[t] = sum(seating[:, t])
    return result


def swap(seating, m, p1, p2):
    i, j = m * POSITIONS, (m+1) * POSITIONS
    seating[p1, i:j], seating[p2, i:j] = seating[p2, i:j].copy(), seating[p1, i:j].copy()


def blind_step(seating):
    result = seating.copy()
    swap(result, numpy.random.choice(MEALS), numpy.random.choice(PERSONS), numpy.random.choice(PERSONS))
    return result


def candidate_step(seating):
    result = seating.copy()
    c = candidates(seating)
    swap(result, numpy.random.choice(MEALS), numpy.random.choice(c), numpy.random.choice(PERSONS))
    return result


def energy_sum(seating):
    n = neighbourness(seating)
    return sum(n[n > 1])


def energy_square(seating):
    return energy_sum(seating) ** 2


def candidates(seating):
    n = neighbourness(seating)
    return numpy.where(n == n.max())[0]


def search(start, step=blind_step, energy=energy_sum, n=10000):
    print "Searching... ",
    seating = start

    e = energy(seating)
    for t in range(n):
        candidate = step(seating)
        new_e = energy(candidate)
        if new_e < e:
            seating = candidate
            e = new_e
            print e,
    print "Done"
    return seating


def dump(seating):
    for m in range(MEALS):
        print "-- %d" % m
        for p in range(POSITIONS):
            print "   ", (numpy.where(seating[:, (m*POSITIONS + p)] == 1)[0])


def main():
    start = initial()
    print start
    dump(start)
    seating = search(start)

    print persons_at_each_table(seating)
    print seating
    dump(seating)

    n = neighbourness(seating)
    print n.max()
    print len(numpy.where(n == n.max())[0])

    n = neighbourness(seating)
    n[n == 1] = 0
    print n.sum(axis=0)

if __name__ == '__main__':
    main()
