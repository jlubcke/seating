from ortools.constraint_solver import pywrapcp


NUMBER_OF_PERSONS = 8
NUMBER_OF_MEALS = 3
NUMBER_OF_TABLES = 2


def seating():
    # Constraint programming engine
    solver = pywrapcp.Solver('Seating')

    v = []
    for m in range(NUMBER_OF_MEALS):
        tmp = []
        for p in range(NUMBER_OF_PERSONS):
            tmp.append(solver.IntVar(range(NUMBER_OF_PERSONS), '<p%sm%s>' % (p, m)))
        solver.Add(solver.AllDifferent(tmp))
        v.append(tmp)

    for p1 in range(NUMBER_OF_PERSONS):
#        for p2 in range(NUMBER_OF_PERSONS):

            tmp = []
            for m in v:
                tmp.append(m[p1])
            solver.Add(solver.AllDifferent(tmp))

    #sum_value = solver.Sum([kBase*kBase*kBase*t, kBase*kBase*r, kBase*u, e])
    #solver.Add(sum_terms == sum_value)

    db = solver.Phase([p for p in m for m in v],
                      solver.INT_VAR_DEFAULT,
                      solver.INT_VALUE_DEFAULT)
    solver.NewSearch(db)

    if solver.NextSolution():
        for m in v:
            print m
    else:
        print 'Cannot solve problem.'

    solver.EndSearch()

    return

if __name__ == '__main__':
    seating()
