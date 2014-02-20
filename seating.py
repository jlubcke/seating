from ortools.constraint_solver import pywrapcp


def seating():
    # Constraint programming engine
    solver = pywrapcp.Solver('Seating');

    # Decision variables
    places = range(0, 4)
    a = solver.IntVar(places, 'a')
    b = solver.IntVar(places, 'b')
    c = solver.IntVar(places, 'c')
    d = solver.IntVar(places, 'd')

    persons = [a, b, c, d]
    solver.Add(solver.AllDifferent(persons))

    #sum_value = solver.Sum([kBase*kBase*kBase*t, kBase*kBase*r, kBase*u, e])
    #solver.Add(sum_terms == sum_value)

    db = solver.Phase(persons, solver.INT_VAR_DEFAULT,
                      solver.INT_VALUE_DEFAULT)
    solver.NewSearch(db)

    if solver.NextSolution():
        print persons
    else:
        print 'Cannot solve problem.'

    solver.EndSearch()

    return

if __name__ == '__main__':
    seating()
