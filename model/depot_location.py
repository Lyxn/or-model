from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Optimal objective value = %f" % solver.Objective().Value())


def has_val(t, i, j):
    return i in t and j in t[i]


def run():
    # Solver
    solver = pywraplp.Solver('depot_location',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    # Context
    factory_name = ["Liverpool", "Brighton"]
    depot_name = ["Newcastle", "Birmingham", "London", "Exeter"]
    factory_depot = {
        0: {0: 0.5, 1: 0.5, 2: 1.0, 3: 0.2},
        1: {1: 0.3, 2: 0.5, 3: 0.2}}
    customer_supplier = {
        0: {0: 1.0, 1: 2.0, 3: 1.0},
        1: {2: 1.5, 3: 0.5, 4: 1.5},
        2: {0: 1.5, 2: 0.5, 3: 0.5, 4: 2.0, 5: 0.2},
        3: {0: 2.0, 2: 1.5, 3: 1.0, 5: 1.5},
        4: {3: 0.5, 4: 0.5, 5: 0.5},
        5: {0: 1.0, 2: 1.0, 4: 1.5, 5: 1.5},
    }

    num_factories = 2
    num_depots = 4
    num_suppliers = num_factories + num_depots
    num_customers = 6
    factory_limit = [150, 200]
    depot_limit = [70, 50, 100, 40]
    demand = [50, 10, 40, 35, 60, 20]
    max_sup = max(factory_limit)

    # Variable & Object
    xm = {}
    ym = {}
    total_cost = 0
    for i in range(num_factories):
        for j in range(num_depots):
            if not has_val(factory_depot, i, j):
                continue
            xm[(i, j)] = solver.NumVar(0, max_sup, "x_%d_%d" % (i, j))
            total_cost += xm[(i, j)] * factory_depot[i][j]

    for i in range(num_customers):
        for j in range(num_suppliers):
            if not has_val(customer_supplier, i, j):
                continue
            ym[(i, j)] = solver.NumVar(0, max_sup, "y_%d_%d" % (i, j))
            total_cost += ym[(i, j)] * customer_supplier[i][j]

    # Constraint
    # factory
    for i in range(num_factories):
        sup = 0
        for j in range(num_depots):
            if not has_val(factory_depot, i, j):
                continue
            sup += xm[(i, j)]
        for k in range(num_customers):
            if not has_val(customer_supplier, k, i):
                continue
            sup += ym[(k, i)]
        solver.Add(sup <= factory_limit[i])

    # depot
    for j in range(num_depots):
        sup_in = 0
        sup_out = 0
        for i in range(num_factories):
            if not has_val(factory_depot, i, j):
                continue
            sup_in += xm[(i, j)]
        for k in range(num_customers):
            if not has_val(customer_supplier, k, j + 2):
                continue
            sup_out += ym[(k, j + 2)]
        solver.Add(sup_in <= depot_limit[j])
        solver.Add(sup_out <= sup_in)

    # customer
    def get_customer_supply(x):
        cs = 0
        for y in range(num_suppliers):
            if not has_val(customer_supplier, x, y):
                continue
            cs += ym[(x, y)]
        return cs

    def set_customer_demand():
        for x in range(num_customers):
            cs = get_customer_supply(x)
            solver.Add(cs >= demand[x])

    def print_factory():
        for x in range(num_factories):
            out = factory_name[x]
            for y in range(num_depots):
                s = xm[(x, y)].solution_value() if has_val(factory_depot, x, y) else 0
                out += "\t%4.1f" % s
            print(out)

    def print_customer():
        for x in range(num_customers):
            out = "customer %d" % x
            for y in range(num_suppliers):
                s = ym[(x, y)].solution_value() if has_val(customer_supplier, x, y) else 0
                out += "\t%4.1f" % s
            print(out)

    def set_preference():
        for x in {1, 3}:
            solver.Add(ym[(0, x)] == 0)
        for x in {3, 4}:
            solver.Add(ym[(1, x)] == 0)
        # for x in {4, 5}:
        #     solver.Add(ym[(4, x)] == 0)
        for x in {0, 2}:
            solver.Add(ym[(5, x)] == 0)

    def new_depot():
        # Context
        num_new = 3
        new_depot_name = ["Bristol", "Northampton", "Birmingham"]
        new_depot_cost = [12, 4, 3]
        new_depot_limit = [30, 25, 20]
        depot_save = {0: 10, 3: 5}
        new_depot_factory = {
            0: {0: 0.6, 1: 0.4},
            1: {0: 0.4, 1: 0.3},
            2: {0: 0.5, 1: 0.3}
        }
        new_depot_customer = {
            0: {0: 1.2, 1: 0.6, 2: 0.5, 4: 0.3, 5: 0.8},
            1: {1: 0.4, 3: 0.5, 4: 0.6, 5: 0.9},
            2: {0: 1.0, 1: 0.5, 2: 0.5, 3: 1.0, 4: 0.5}
        }

        # open
        xn = {}
        yn = {}
        opn = {}
        new_cost = 0
        for x in range(num_new):
            # factory
            opn_in = 0
            for y in range(num_factories):
                v = solver.NumVar(0, max_sup, "xn_%d_%d" % (x, y))
                xn[(x, y)] = v
                new_cost += v * new_depot_factory[x][y]
                opn_in += v

            # customer
            opn_out = 0
            for y in range(num_customers):
                if not has_val(new_depot_customer, x, y):
                    continue
                v = solver.NumVar(0, max_sup, "yn_%d_%d" % (x, y))
                yn[(x, y)] = v
                new_cost += v * new_depot_customer[x][y]
                opn_out += v

            # constraint
            solver.Add(opn_in <= new_depot_limit[x])
            solver.Add(opn_out <= opn_in)

            # open
            opn[x] = solver.BoolVar("open_%d" % x)
            solver.Add(opn_in <= max_sup * opn[x])
            new_cost += opn[x] * new_depot_cost[x]

        solver.Add(opn[2] == 1)

        # close
        cls = {}
        for x in {0, 3}:
            cls[x] = solver.BoolVar("close_%d" % x)
            cls_sup = 0
            for y in range(num_factories):
                if not has_val(factory_depot, y, x):
                    continue
                cls_sup += xm[(y, x)]
            solver.Add(cls_sup <= max_sup * (1 - cls[x]))
            # saving
            new_cost -= cls[x] * depot_save[x]

        # depot
        expr = opn[0] + opn[1] <= cls[0] + cls[3]
        solver.Add(expr)

        # demand
        def get_customer_supply_new(c):
            cs = 0
            for d in range(num_new):
                if not has_val(new_depot_customer, d, c):
                    continue
                cs += yn[(d, c)]
            return cs

        for t in range(num_customers):
            ss = get_customer_supply(t) + get_customer_supply_new(t)
            solver.Add(ss >= demand[t])

        def print_solution():
            out = "Open"
            for s, t in opn.items():
                out += "\t%s:%d" % (new_depot_name[s], t.solution_value())
            print(out)
            out = "Close"
            for s, t in cls.items():
                out += "\t%s:%d" % (depot_name[s], t.solution_value())
            print(out)
            for t in range(num_factories):
                out = factory_name[t]
                for s in range(num_new):
                    ret = xn[(s, t)].solution_value()
                    out += "\t%4.1f" % ret
                print(out)
            for t in range(num_customers):
                out = "customer %d" % t
                for s in range(num_new):
                    ret = yn[(s, t)].solution_value() if has_val(new_depot_customer, s, t) else 0
                    out += "\t%4.1f" % ret
                print(out)

        return new_cost, print_solution

    # set_preference()
    # set_customer_demand()

    # Object
    new_total_cost, print_new_depot = new_depot()
    total_cost += new_total_cost
    solver.Minimize(total_cost)

    solver.Solve()
    print_solver(solver)
    print_factory()
    print_customer()
    print_new_depot()


if __name__ == '__main__':
    run()
