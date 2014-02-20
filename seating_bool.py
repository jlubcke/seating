from ortools.constraint_solver import pywrapcp


NUMBER_OF_PERSONS = 20
NUMBER_OF_SEATS = NUMBER_OF_PERSONS
NUMBER_OF_MEALS = 8
NUMBER_OF_TABLES = 2


def seating():
    # Constraint programming engine
    solver = pywrapcp.Solver('Seating')

    v = []
    for m in range(NUMBER_OF_MEALS):
        persons = []
        for p in range(NUMBER_OF_PERSONS):
            seats = []
            for s in range(NUMBER_OF_SEATS):
                seats.append(solver.IntVar([0, 1], '<p%sm%ss%s>' % (p, m, s)))
            solver.Add(solver.Sum(seats) == 1)
            persons.append(seats)

        for seat in zip(*persons):
            solver.Add(solver.Sum(seat) == 1)

        v.append(persons)

    def is_neighbour(s1, s2):
        return abs(s1 - s2) == 1

    for p1 in range(NUMBER_OF_PERSONS):
        for p2 in range(NUMBER_OF_PERSONS):
            terms = []
            for m in range(NUMBER_OF_MEALS):
                for s1 in range(NUMBER_OF_SEATS):
                    for s2 in range(NUMBER_OF_SEATS):
                        if is_neighbour(s1, s2):
                            terms.append(v[m][p1][s1] * v[m][p2][s2])
            solver.Add(solver.Sum(terms) <= 1)

    #sum_value = solver.Sum([kBase*kBase*kBase*t, kBase*kBase*r, kBase*u, e])
    #solver.Add(sum_terms == sum_value)

    print "Solving..."

    db = solver.Phase([s for m in v for p in m for s in p],
                      solver.INT_VAR_DEFAULT,
                      solver.INT_VALUE_DEFAULT)
    solver.NewSearch(db)

    if solver.NextSolution():
        #solution = solver.Assignment()
        for m in v:
            print
            for i, p in enumerate(m):
                for j, v in enumerate(p):
                    if v.Value():
                        print "%s: %s" % (i, j)

    else:
        print 'Cannot solve problem.'

    solver.EndSearch()

    return

if __name__ == '__main__':
    seating()
