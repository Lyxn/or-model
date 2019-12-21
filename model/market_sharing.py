from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Optimal objective value = %f" % solver.Objective().Value())


def run():
    # Solver
    solver = pywraplp.Solver('mining',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    # Context
    num_retails = 23
    num_region = 3
    regions = [8, 18, 23]
    oils = [9, 13, 14, 17, 18, 19, 23, 21, 9, 11,
            17, 18, 18, 17, 22, 24, 36, 43, 6, 15,
            15, 25, 39]
    points = [11, 47, 44, 25, 10, 26, 26, 54, 18, 51,
              20, 105, 7, 16, 34, 100, 50, 21, 11, 19,
              14, 10, 11]
    spirits = [34, 411, 82, 157, 5, 183, 14, 215, 102, 21,
               54, 0, 6, 96, 118, 112, 535, 8, 53, 28,
               69, 65, 27]
    growth = [1, 1, 1, 0, 1, 1, 0, 0, 0, 1,
              0, 0, 0, 0, 1, 0, 0, 0, 0, 1,
              0, 0, 0]
    total_oil0 = sum(oils[0:8])
    total_oil1 = sum(oils[8:18])
    total_oil2 = sum(oils[18:23])
    total_points = sum(points)
    total_spirits = sum(spirits)
    total_growth1 = sum(growth)
    total_growth0 = num_retails - total_growth1

    # Variable
    xm = {}
    for i in range(num_retails):
        xm[i] = solver.BoolVar("x_%d" % i)

    # Market Sharing
    # point
    point0 = sum(xm[i] * points[i] for i in range(num_retails))
    # spirit
    spirit0 = sum(xm[i] * spirits[i] for i in range(num_retails))
    # oil
    oil0 = sum(xm[i] * oils[i] for i in range(0, 8))
    oil1 = sum(xm[i] * oils[i] for i in range(8, 18))
    oil2 = sum(xm[i] * oils[i] for i in range(18, 23))
    # growth
    growth1 = sum(xm[i] for i in range(num_retails) if growth[i] == 1)
    growth0 = sum(xm[i] for i in range(num_retails) if growth[i] == 0)

    num_shares = 7
    share_name = "point spirit oil_1 oil_2 oil_3 growth_a growth_b"
    share_name = share_name.split()
    shares = [point0, spirit0, oil0, oil1, oil2, growth1, growth0]
    totals = [total_points, total_spirits, total_oil0, total_oil1, total_oil2, total_growth1, total_growth0]
    totals = [float(totals[i]) for i in range(num_shares)]
    ratios = [shares[i] / totals[i] for i in range(num_shares)]
    deviations = [x - 0.4 for x in ratios]

    def min_mae():
        mae = solver.NumVar(0, 1, "mae")
        for dvt in deviations:
            solver.Add(dvt <= mae)
            solver.Add(-dvt <= mae)
        solver.Minimize(mae)

    # Solve
    def print_variable():
        out = "Retail:"
        for x in range(num_retails):
            out += "\t%d" % xm[x].solution_value()
        print(out)

    def print_sharing(name, share, total):
        print("%s\t%d\t%d\t%.3f" % (name, share, total, share / total))

    def print_market():
        for i in range(num_shares):
            print_sharing(share_name[i], shares[i].solution_value(), totals[i])

    min_mae()
    solver.Solve()
    print_solver(solver)
    print_variable()
    print_market()


if __name__ == '__main__':
    run()
