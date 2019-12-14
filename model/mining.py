from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Optimal objective value = %f" % solver.Objective().Value())


def print_variable(variables, mine, year):
    for i in range(mine):
        out = "Mine %d:" % i
        for t in range(year):
            var = variables[(i, t)]
            out += "\t%.3f" % var.solution_value()
        print(out)


def print_year_var(variables, year):
    out = "Year:"
    for t in range(year):
        var = variables[t]
        out += "\t%.3f" % var.solution_value()
    print(out)


def run():
    # Solver
    solver = pywraplp.Solver('mining',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    # Context
    num_mine = 4
    num_year = 5
    year_cost = [5, 4, 4, 5]  # million
    max_mine = [2, 2.5, 1.3, 3]  # million
    max_total = sum(max_mine)
    mine_quality = [1.0, 0.7, 1.5, 0.5]
    year_quality = [0.9, 0.8, 1.2, 0.6, 1.0]

    # Variable
    delta = {}
    gamma = {}
    x0 = {}
    for i in range(num_mine):
        for t in range(num_year):
            delta[(i, t)] = solver.BoolVar("d_%d_%d" % (i, t))
            gamma[(i, t)] = solver.BoolVar("g_%d_%d" % (i, t))
            x0[(i, t)] = solver.NumVar(0, max_mine[i], "x_%d_%d" % (i, t))
    qt = {}
    for t in range(num_year):
        qt[t] = solver.NumVar(0, max_total, "q_%d" % t)

    # Constraint
    for i in range(num_mine):
        for t in range(num_year):
            solver.Add(x0[(i, t)] <= max_mine[i] * delta[(i, t)], "c1_%d_%d" % (i, t))

    # open at most 3 mines every year
    for t in range(num_year):
        s = 0
        for i in range(num_mine):
            s += delta[(i, t)]
        solver.Add(s <= 3, "c2_%d" % t)

    # consistency
    for i in range(num_mine):
        for t in range(num_year):
            solver.Add(delta[(i, t)] <= gamma[(i, t)], "c3_%d_%d" % (i, t))

    for i in range(num_mine):
        for t in range(num_year - 1):
            solver.Add(gamma[(i, t + 1)] <= gamma[(i, t)], "c4_%d_%d" % (i, t))

    # year output
    for t in range(num_year):
        s = sum(x0[(i, t)] for i in range(num_mine))
        solver.Add(s == qt[t], "c5_%d" % t)

    # blend quality
    for t in range(num_year):
        s = sum(x0[(i, t)] * mine_quality[i] for i in range(num_mine))
        solver.Add(s == qt[t] * year_quality[t], "c6_%d" % t)

    # Object
    obj = 0
    for t in range(num_year):
        rate = 0.9 ** t
        for i in range(num_mine):
            obj -= rate * year_cost[i] * gamma[(i, t)]
        obj += 10 * rate * qt[t]
    solver.Maximize(obj)
    solver.Solve()
    print_solver(solver)
    # print_variable(delta, num_mine, num_year)
    # print_variable(gamma, num_mine, num_year)
    print_variable(x0, num_mine, num_year)
    print_year_var(qt, num_year)


if __name__ == '__main__':
    run()
