from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Optimal objective value = %f" % solver.Objective().Value())


def run():
    # Solver
    solver = pywraplp.Solver('optimize_constraint',
                             pywraplp.Solver.CLP_LINEAR_PROGRAMMING)

    # Context
    num_var = 9
    ceilings = [{1, 2, 3}, {1, 2, 4, 8}, {1, 2, 6, 7}, {1, 3, 5, 6}, {2, 3, 4, 6}, {2, 5, 6, 7, 8}]
    roofs = [{1, 2, 3, 8}, {1, 2, 5, 7}, {1, 3, 4, 7}, {1, 5, 6, 7, 8}, {2, 3, 4, 5}, {3, 4, 6, 7, 8}]

    # Variable
    ub = 100
    a = {}
    for i in range(num_var):
        a[i] = solver.NumVar(0, ub, "a_%d" % i)

    # Constraint
    for i in range(1, num_var - 1):
        solver.Add(a[i] >= a[i + 1])

    # ceilings
    for ceiling in ceilings:
        expr = sum(a[i] for i in ceiling) <= a[0]
        solver.Add(expr)
    # roofs
    for roof in roofs:
        expr = sum(a[i] for i in roof) >= a[0] + 1
        solver.Add(expr)

    # Object
    obj = a[0] - a[3] - a[5]
    # obj = sum(a[i] for i in range(1, num_var))
    solver.Minimize(obj)

    # Solve
    def print_variable():
        a0 = "a0:\t%d" % a[0].solution_value()
        print(a0)
        out = "ai:"
        for i in range(1, num_var):
            out += "\t%d" % a[i].solution_value()
        print(out)

    solver.Solve()
    print_solver(solver)
    print_variable()


if __name__ == '__main__':
    run()
