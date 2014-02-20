from ortools.constraint_solver import pywrapcp


NUMBER_OF_PERSONS = 10
NUMBER_OF_SEATS = NUMBER_OF_PERSONS
NUMBER_OF_MEALS = 4


def is_neighbour(i, j):
    return abs(i - j) == 1


def seating():
    solver = pywrapcp.Solver('Seating')

    v = []
    for m in range(NUMBER_OF_MEALS):
        persons = []
        for p in range(NUMBER_OF_PERSONS):
            seats = [solver.IntVar([0, 1], '<m%sp%ss%s>' % (m, p, s))
                     for s in range(NUMBER_OF_SEATS)]
            # Place person at exactly one place
            solver.Add(solver.Sum(seats) == 1)
            persons.append(seats)

        for seat in zip(*persons):
            # Only one person at each place
            solver.Add(solver.Sum(seat) == 1)

        v.append(persons)

    for p1 in range(NUMBER_OF_PERSONS):
        for p2 in range(NUMBER_OF_PERSONS):
            terms = [v[m][p1][s1] * v[m][p2][s2]
                     for m in range(NUMBER_OF_MEALS)
                     for s1 in range(NUMBER_OF_SEATS)
                     for s2 in range(NUMBER_OF_SEATS)
                     if is_neighbour(s1, s2)]
            # Neighbours not more than once
            solver.Add(solver.Sum(terms) <= 1)

    print "Solving..."

    db = solver.Phase([s for m in v for p in m for s in p],
                      solver.INT_VAR_DEFAULT,
                      solver.INT_VALUE_DEFAULT)
    solver.NewSearch(db)

    if solver.NextSolution():
        for m in v:
            print
            for i, p in enumerate(m):
                for j, s in enumerate(p):
                    if s.Value():
                        print "%s: %s" % (i, j)
    else:
        print 'Cannot solve problem.'

    solver.EndSearch()


if __name__ == '__main__':
    seating()
