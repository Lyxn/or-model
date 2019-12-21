from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Optimal objective value = %f" % solver.Objective().Value())


def run():
    # Solver
    solver = pywraplp.Solver('hydro_power',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    # Context
    num_periods = 5
    period_hours = [6, 3, 6, 3, 6]
    period_demand = [15, 30, 25, 40, 27]
    # thermal
    num_types = 3
    num_units = [12, 10, 5]
    min_level = [0.85, 1.25, 1.5]
    max_level = [2, 1.75, 4]
    cost_per_hour = [1, 2.6, 3]
    cost_per_hour_over = [2, 1.3, 3]
    cost_start = [2, 1, 0.5]
    overload_rate = 1.15
    # hydro
    num_hydro = 2
    hydro_level = [0.9, 1.4]
    hydro_cost_per_hour = [0.09, 0.15]
    hydro_start_cost = [1.5, 1.2]
    hydro_reduce_per_hour = [0.31, 0.47]

    # Variable
    # thermal
    xt = {}  # units of generator
    yt = {}  # units of free start-up
    wt = {}  # total load

    def set_thermal_variable():
        for t in range(num_periods):
            for i in range(num_types):
                xt[(i, t)] = solver.IntVar(0, num_units[i], "x_%d_%d" % (i, t))
                yt[(i, t)] = solver.IntVar(0, num_units[i], "y_%d_%d" % (i, t))
                wt[(i, t)] = solver.NumVar(0, num_units[i] * max_level[i], "w_%d_%d" % (i, t))

    # hydro
    ht = {}
    st = {}
    lt = {}
    pt = {}
    max_thermal_level = sum(num_units[i] * max_level[i] for i in range(num_types))

    def set_hydro_variable():
        for t in range(num_periods):
            for i in range(num_hydro):
                ht[(i, t)] = solver.BoolVar("hydro_%d_%d" % (i, t))
                st[(i, t)] = solver.BoolVar("hydro_start_%d_%d" % (i, t))
            lt[t] = solver.NumVar(15, 20, "height_%d" % t)
            pt[t] = solver.NumVar(0, max_thermal_level, "pump_%d" % t)

    # Constraint
    # free start-up
    def set_thermal_start():
        for t in range(num_periods):
            for i in range(num_types):
                solver.Add(yt[(i, t)] <= xt[(i, t)])
                last = xt[(i, t - 1)] if t > 0 else xt[(i, num_periods - 1)]
                solver.Add(yt[(i, t)] <= last)

    def set_hydro_start():
        for t in range(num_periods):
            for i in range(num_hydro):
                last = ht[(i, t - 1)] if t > 0 else ht[(i, num_periods - 1)]
                solver.Add(st[(i, t)] >= ht[(i, t)] - last)

    # period demand
    def get_thermal_load(t):
        return sum(wt[(y, t)] for y in range(num_types))

    def get_thermal_max_load(t):
        return sum(xt[(y, t)] * max_level[y] for y in range(num_types))

    def get_hydro_load(t):
        return sum(ht[(y, t)] * hydro_level[y] for y in range(num_hydro))

    def set_thermal_level():
        for t in range(num_periods):
            for i in range(num_types):
                expr_upper = wt[(i, t)] <= xt[(i, t)] * max_level[i]
                solver.Add(expr_upper)
                expr_lower = wt[(i, t)] >= xt[(i, t)] * min_level[i]
                solver.Add(expr_lower)

    def set_demand_thermal():
        for t in range(num_periods):
            load = get_thermal_load(t)
            solver.Add(load >= period_demand[t], "demand_%d" % t)
            max_load = get_thermal_max_load(t)
            solver.Add(max_load >= period_demand[t] * overload_rate, "over_%d" % t)

    def set_demand_hydro():
        for t in range(num_periods):
            load = get_thermal_load(t) + get_hydro_load(t) - pt[t]
            solver.Add(load >= period_demand[t], "demand_%d" % t)
            max_load = get_thermal_max_load(t) + sum(hydro_level)
            solver.Add(max_load >= period_demand[t] * overload_rate, "over_%d" % t)

    def get_reservoir_reduce(t):
        return sum(period_hours[t] * hydro_reduce_per_hour[i] * ht[(i, t)] for i in range(num_hydro))

    def set_reservoir_level():
        solver.Add(lt[0] == 16)
        for t in range(num_periods):
            level = lt[t] + period_hours[t] * pt[t] / 3 - get_reservoir_reduce(t)
            next = lt[t + 1] if t < num_periods - 1 else lt[0]
            solver.Add(level == next)

    # Objective
    def get_thermal_cost():
        cst = 0
        for t in range(num_periods):
            for i in range(num_types):
                cst += period_hours[t] * \
                       (xt[(i, t)] * cost_per_hour[i] +
                        (wt[(i, t)] - xt[(i, t)] * min_level[i]) * cost_per_hour_over[i])
                cst += (xt[(i, t)] - yt[(i, t)]) * cost_start[i]
        return cst

    def get_hydro_cost():
        cst = 0
        for t in range(num_periods):
            for i in range(num_hydro):
                cst += period_hours[t] * hydro_cost_per_hour[i] * ht[(i, t)]
                cst += hydro_start_cost[i] * st[(i, t)]
        return cst

    def run_thermal():
        set_thermal_variable()
        set_thermal_start()
        set_thermal_level()
        set_demand_thermal()
        total_cost = get_thermal_cost()
        solver.Minimize(total_cost)

    def run_hydro():
        set_thermal_variable()
        set_thermal_start()
        set_thermal_level()
        set_hydro_variable()
        set_hydro_start()
        set_reservoir_level()
        set_demand_hydro()
        total_cost = get_thermal_cost() + get_hydro_cost()
        solver.Minimize(total_cost)

    def print_thermal():
        out_xt = "Thermal"
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

    def print_hydro():
        out_ht = "Hydro"
        out_st = "Start-up"
        for x in range(num_hydro):
            out_h = "%d:" % x
            out_s = "%d:" % x
            for y in range(num_periods):
                hv = ht[(x, y)].solution_value()
                sv = st[(x, y)].solution_value()
                out_h += "\t%d" % hv
                out_s += "\t%d" % sv
            out_ht += "\n%s" % out_h
            out_st += "\n%s" % out_s
        print(out_ht)
        print(out_st)

        out_lt = "Reservoir:"
        out_pt = "Pump:"
        for y in range(num_periods):
            out_lt += "\t%4.2f" % lt[y].solution_value()
            out_pt += "\t%4.2f" % pt[y].solution_value()
        print(out_lt)
        print(out_pt)

    # Solver
    # run_thermal()
    run_hydro()
    solver.Solve()
    print_solver(solver)
    print_thermal()
    print_hydro()


if __name__ == '__main__':
    run()
