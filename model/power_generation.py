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
    num_periods = 5
    period_hours = [6, 3, 6, 3, 6]
    period_demand = [15, 30, 25, 40, 27]
    num_types = 3
    num_units = [12, 10, 5]
    min_level = [0.85, 1.25, 1.5]
    max_level = [2, 1.75, 4]
    cost_per_hour = [1, 2.6, 3]
    cost_per_hour_over = [2, 1.3, 3]
    cost_start = [2, 1, 0.5]
    overload_rate = 1.15

    # Variable
    xt = {}  # units of generator
    yt = {}  # units of free start-up
    wt = {}  # total load
    for t in range(num_periods):
        for i in range(num_types):
            xt[(i, t)] = solver.IntVar(0, num_units[i], "x_%d_%d" % (i, t))
            yt[(i, t)] = solver.IntVar(0, num_units[i], "y_%d_%d" % (i, t))
            wt[(i, t)] = solver.NumVar(0, num_units[i] * max_level[i], "w_%d_%d" % (i, t))

    # Constraint
    # free start-up
    for t in range(num_periods):
        for i in range(num_types):
            solver.Add(yt[(i, t)] <= xt[(i, t)])
            if t == 0:
                solver.Add(yt[(i, t)] <= xt[(i, num_periods - 1)])
            else:
                solver.Add(yt[(i, t)] <= xt[(i, t - 1)])

    # period demand
    def get_period_load(x):
        return sum(wt[(y, x)] for y in range(num_types))

    def get_period_max_load(x):
        return sum(xt[(y, x)] * max_level[y] for y in range(num_types))

    for t in range(num_periods):
        load = get_period_load(t)
        solver.Add(load >= period_demand[t], "demand_%d" % t)
        max_load = get_period_max_load(t)
        solver.Add(max_load >= period_demand[t] * overload_rate, "over_%d" % t)

        for i in range(num_types):
            expr_upper = wt[(i, t)] <= xt[(i, t)] * max_level[i]
            solver.Add(expr_upper)
            expr_lower = wt[(i, t)] >= xt[(i, t)] * min_level[i]
            solver.Add(expr_lower)

    # Objective
    total_cost = 0
    for t in range(num_periods):
        for i in range(num_types):
            total_cost += period_hours[t] * \
                          (xt[(i, t)] * cost_per_hour[i] +
                           (wt[(i, t)] - xt[(i, t)] * min_level[i]) * cost_per_hour_over[i])
            total_cost += (xt[(i, t)] - yt[(i, t)]) * cost_start[i]
    solver.Minimize(total_cost)

    def print_variable():
        out_xt = "Unit"
        out_yt = "Free Start-up"
        out_wt = "Load"
        out_mt = "Margin"
        for x in range(num_types):
            out_x = "%d:" % x
            out_y = "%d:" % x
            out_w = "%d:" % x
            out_m = "%d:" % x
            for y in range(num_periods):
                xv = xt[(x, y)].solution_value()
                yv = yt[(x, y)].solution_value()
                wv = wt[(x, y)].solution_value()
                out_x += "\t%d" % xv
                out_y += "\t%d" % yv
                out_w += "\t%4.2f" % wv
                out_m += "\t%4.2f" % (xv * max_level[x] - wv)
            out_xt += "\n%s" % out_x
            out_yt += "\n%s" % out_y
            out_wt += "\n%s" % out_w
            out_mt += "\n%s" % out_m
        print(out_xt)
        # print(out_yt)
        print(out_wt)
        print(out_mt)

    def print_period():
        out_load = "Load:"
        out_max = "Max:"
        for y in range(num_periods):
            cur_load = get_period_load(y)
            load_upper = get_period_max_load(y)
            out_load += "\t%4.2f" % cur_load.solution_value()
            out_max += "\t%4.2f" % load_upper.solution_value()
        print(out_load)
        print(out_max)

    def print_constraint():
        for y in range(num_periods):
            # name = "over_%d" % y
            name = "demand_%d" % y
            constraint = solver.LookupConstraint(name)
            print(constraint.DualValue())

    solver.Solve()
    print_solver(solver)
    print_variable()
    # print_period()
    # print_constraint()


if __name__ == '__main__':
    run()
