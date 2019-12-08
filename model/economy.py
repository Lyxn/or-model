import numpy as np

from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Optimal objective value = %f" % solver.Objective().Value())


def solver_linear_system(a, b):
    solver = pywraplp.Solver('linear_system',
                             pywraplp.Solver.CLP_LINEAR_PROGRAMMING)
    num_cols = len(a[0])
    num_rows = len(b)
    variables = [solver.NumVar(0, solver.Infinity(), "x_%d" % j) for j in range(num_cols)]
    for k in range(num_rows):
        lhs = sum(a[k][j] * variables[j] for j in range(num_cols))
        solver.Add(lhs == b[k])
    solver.Minimize(0)
    solver.Solve()
    return [x.solution_value() for x in variables]


def run():
    # Solver
    solver = pywraplp.Solver('economic_planning',
                             pywraplp.Solver.CLP_LINEAR_PROGRAMMING)
    infinity = solver.Infinity()

    # Context
    num_industries = 3
    num_years = 5
    product_mat = [[0.1, 0.5, 0.4], [0.1, 0.1, 0.2], [0.2, 0.1, 0.2], [0.6, 0.3, 0.2]]
    capacity_mat = [[0.0, 0.7, 0.9], [0.1, 0.1, 0.2], [0.2, 0.1, 0.2], [0.4, 0.2, 0.1]]
    stock0 = [150, 80, 100]
    capacity0 = [300, 350, 280]
    manpower_limit = 470
    consumption = [60, 60, 30]

    def calc_final_product(b):
        num = len(b)
        a = np.zeros((num, num))
        for i in range(num):
            for j in range(num):
                if i == j:
                    a[i][j] = 1 - product_mat[i][j]
                else:
                    a[i][j] = - product_mat[i][j]
        return solver_linear_system(a, b)

    final_product = calc_final_product(consumption)
    print("final stock:", final_product)

    # Variable
    xt = {}
    st = {}
    yt = {}
    for i in range(num_industries):
        for t in range(num_years):
            xt[(i, t + 1)] = solver.NumVar(0, infinity, "x_%d_%d" % (i, t))
            st[(i, t + 1)] = solver.NumVar(0, infinity, "s_%d_%d" % (i, t))
            yt[(i, t + 2)] = solver.NumVar(0, infinity, "y_%d_%d" % (i, t))
        st[(i, 0)] = stock0[i]

    # Constraint
    def calc_industry_input(k, t):
        lhs = 0
        for j in range(num_industries):
            lhs += xt[(j, t + 1)] * product_mat[k][j] + yt[(j, t + 2)] * capacity_mat[k][j]
        return lhs

    # Manpower
    def add_manpower_limit():
        for t in range(num_years):
            lhs = calc_industry_input(3, t)
            solver.Add(lhs <= manpower_limit, "manpower_%d" % t)

    # Stock
    def add_consumption(b):
        for t in range(num_years):
            for i in range(num_industries):
                input = calc_industry_input(i, t)
                expr = st[(i, t + 1)] == st[(i, t)] - input - b[i] + xt[(i, t + 1)]
                solver.Add(expr, "consumption_%d_%d" % (i, t))

    # Capacity
    for t in range(num_years):
        for i in range(num_industries):
            caps = sum(yt[(i, l)] for l in range(2, t + 1))
            expr = xt[(i, t + 1)] <= capacity0[i] + caps
            solver.Add(expr, "capacity_%d_%d" % (i, t))
    # Final
    for i in range(num_industries):
        solver.Add(xt[(i, 5)] >= final_product[i])
        solver.Add(yt[(i, 6)] == 0)

    # Object
    def max_capacity():
        add_manpower_limit()
        add_consumption(consumption)
        caps = sum(yt[(i, l)] for i in range(num_industries) for l in range(2, num_years + 1))
        solver.Maximize(caps)

    def max_product():
        add_manpower_limit()
        b = [0, 0, 0]
        add_consumption(b)
        prod = sum(xt[(i, t)] for i in range(num_industries) for t in range(4, 6))
        solver.Maximize(prod)

    def max_manpower():
        add_consumption(consumption)
        power = sum(calc_industry_input(3, t) for t in range(num_years))
        solver.Maximize(power)

    def print_capacity():
        for i in range(num_industries):
            out = "cap %d:" % i
            for t in range(1, num_years + 1):
                caps = sum(yt[(i, l)].solution_value() for l in range(2, t + 1)) + capacity0[i]
                out = "\t%.2f" % caps
            print(out)

    def print_extra_capacity():
        for i in range(num_industries):
            out = "extra %d:" % i
            for t in range(num_years):
                out = "\t%.2f" % yt[(i, t + 2)].solution_value()
            print(out)

    def print_output():
        for i in range(num_industries):
            out = "output %d:" % i
            for t in range(1, num_years + 1):
                out += "%s\t%.2f" % xt[(i, t)].solution_value()
            print(out)

    def print_stock():
        for i in range(num_industries):
            out = "stock %d:" % i
            for t in range(1, num_years + 1):
                out += "\t%.2f" % st[(i, t)].solution_value()
            print(out)

    def print_input(k, prefix="input"):
        out = "%s %d:" % (prefix, k)
        for t in range(1, num_years + 1):
            lhs = 0
            for j in range(num_industries):
                lhs += xt[(j, t)].solution_value() * product_mat[k][j] + \
                       yt[(j, t + 1)].solution_value() * capacity_mat[k][j]
            out += "\t%.2f" % lhs
        print(out)

    def print_manpower():
        print_input(3, "manpower")

    def print_variable():
        print_extra_capacity()
        print_capacity()
        print_output()
        print_stock()
        print_manpower()
        for i in range(num_industries):
            print_input(i)

    # max_capacity()
    # max_product()
    max_manpower()

    solver.Solve()
    print_solver(solver)
    print_variable()


if __name__ == '__main__':
    run()
