from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Objective value = %f" % solver.Objective().Value())


def run():
    # Solver
    solver = pywraplp.Solver('lost_baggage',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    # Context
    time_limit = 120
    airport_name = ["Heathrow", "Harrow", "Ealing", "Holborn", "Sutton",
                    "Dartford", "Bromley", "Greenwich", "Barking", "Hammersmith",
                    "Kingston", "Richmond", "Battersea", "Islington", "Woolwich"]
    num_airports = len(airport_name)
    num_vans = 2
    eta_map = [
        [20],
        [25, 15],
        [35, 35, 30],
        [65, 60, 50, 45],
        [90, 55, 70, 60, 46],
        [85, 57, 55, 53, 15, 15],
        [80, 85, 50, 55, 45, 15, 17],
        [86, 90, 65, 47, 75, 25, 25, 25],
        [25, 25, 10, 12, 25, 45, 41, 40, 65],
        [35, 35, 25, 22, 11, 65, 25, 34, 70, 20],
        [20, 30, 15, 20, 19, 53, 33, 32, 72, 8, 5],
        [44, 37, 24, 12, 15, 43, 27, 20, 61, 7, 12, 14],
        [35, 20, 20, 10, 25, 63, 45, 30, 45, 15, 45, 34, 30],
        [82, 40, 90, 21, 25, 70, 30, 10, 13, 25, 65, 56, 40, 27]
    ]

    def get_eta(i, j):
        return eta_map[j - 1][i] if i < j else eta_map[i - 1][j]

    # Variable
    xk = {}
    for k in range(num_vans):
        for i in range(num_airports - 1):
            for j in range(i + 1, num_airports):
                xk[(k, i, j)] = solver.BoolVar("x_%d_%d_%d" % (k, i, j))
    yk = {}
    zk = {}
    for k in range(num_vans):
        for i in range(1, num_airports):
            yk[(k, i)] = solver.BoolVar("y_%d_%d" % (k, i))
        zk[k] = solver.BoolVar("z_%d" % k)

    # Constraint
    # yes or no
    for k in range(num_vans):
        for i in range(1, num_airports):
            solver.Add(yk[(k, i)] <= zk[k], "use_%d_%d" % (k, i))

    # visit once
    for i in range(1, num_airports):
        lhs = sum(yk[(k, i)] for k in range(num_vans))
        solver.Add(lhs == 1, "once_%d" % i)

    # visit airport
    def add_van_arc(vk):
        for a in range(num_airports):
            arcs = sum(xk[(vk, b, a)] for b in range(a)) + \
                   sum(xk[(vk, a, b)] for b in range(a + 1, num_airports))
            if a == 0:
                solver.Add(arcs == zk[vk], "start_%d" % vk)
            else:
                solver.Add(arcs <= 2 * yk[(vk, a)], "arc_%d_%d" % (vk, a))

    # route
    def get_total_arc(vk):
        total_arc = 0
        for i in range(num_airports - 1):
            for j in range(i + 1, num_airports):
                total_arc += xk[(vk, i, j)]
        return total_arc

    def add_van_route(vk):
        total_arc = get_total_arc(vk)
        rhs = sum(yk[(vk, m)] for m in range(1, num_airports))
        solver.Add(total_arc == rhs)

    for k in range(num_vans):
        add_van_arc(k)
        add_van_route(k)

    # time limit
    def get_total_eta(vk):
        total_eta = 0
        for i in range(num_airports - 1):
            for j in range(i + 1, num_airports):
                total_eta += xk[(vk, i, j)] * get_eta(i, j)
        return total_eta

    van_eta = {}
    max_eta = solver.NumVar(0, time_limit, "max_eta")
    for k in range(num_vans):
        eta = get_total_eta(k)
        solver.Add(eta <= max_eta, "time_%d" % k)
        van_eta[k] = eta

    # van order
    def get_visit(vk):
        return sum(yk[(vk, a)] for a in range(1, num_airports))

    van_visit = [get_visit(k) for k in range(num_vans)]

    def add_constraint_van_order():
        for k in range(num_vans - 1):
            solver.Add(van_visit[k] >= van_visit[k + 1], "visit_%d" % k)

    # Solve
    def print_all_xk():
        for k in range(num_vans):
            print("Van %d" % k)
            print_xk(k)

    def print_xk(k):
        for i in range(num_airports):
            out = "airport %02d:" % i
            out = "%12s" % airport_name[i]
            for j in range(num_airports):
                c = "-"
                if i < j:
                    c = "%d" % xk[(k, i, j)].solution_value()
                elif i == j:
                    c = "+"
                out += "\t%s" % c
            print(out)

    def print_yk():
        for vk in range(num_vans):
            out = "Van %d:" % vk
            for i in range(1, num_airports):
                out += "\t%d" % yk[(vk, i)].solution_value()
            print(out)

    def get_next(k, src, last):
        for f in range(num_airports):
            if f == src or f == last:
                continue
            v = xk[(k, src, f)] if src < f else xk[(k, f, src)]
            if v.solution_value() == 1:
                return f
        return -1

    def find_path(k):
        paths = []
        visits = set()
        for src in range(num_airports):
            if src in visits:
                continue
            path = [src]
            last = -1
            cur = get_next(k, src, last)
            last = src
            if cur == -1:
                continue
            for itr in range(num_airports):
                if cur == src or cur == -1:
                    break
                visits.add(cur)
                path.append(cur)
                nxt = get_next(k, cur, last)
                last = cur
                cur = nxt
            paths.append(path)
        return paths

    def find_all_path(num):
        return dict((x, find_path(x)) for x in range(num))

    def add_subtour(k, cycle):
        num = len(cycle)
        lhs = 0
        for s in range(num - 1):
            for d in range(s + 1, num):
                src = cycle[s]
                dst = cycle[d]
                lhs += xk[(k, src, dst)] if src < dst else xk[(k, dst, src)]
        solver.Add(lhs <= num - 1)

    def add_constraint_subtour(van_paths):
        has_subtour = False
        for k, path in van_paths.items():
            if len(path) > 1:
                has_subtour = True
                for sub in path:
                    if 0 in sub:
                        continue
                    add_subtour(k, sub)
        return has_subtour

    def print_paths(paths):
        for path in paths:
            print(path)

    def print_all_subtour(van_paths):
        for k, subs in van_paths.items():
            print("Van %d" % k)
            print_paths(subs)

    def print_van_eta():
        for k, v in van_eta.items():
            print("Van %d\tETA = %d" % (k, v.solution_value()))

    def get_path_eta(path):
        path_eta = 0
        for i in range(len(path) - 1):
            src = path[i]
            dst = path[i + 1]
            path_eta += get_eta(src, dst)
        return path_eta

    def print_path_eta(van_paths):
        for k, paths in van_paths.items():
            print("Van %d" % k)
            for path in paths:
                path_eta = get_path_eta(path)
                print("ETA = %d" % path_eta)
                print(path)
                print(*[airport_name[x] for x in path], sep="\t")

    add_constraint_van_order()
    # Object
    # obj = sum(van_eta.values())
    obj = max_eta
    # obj = sum(zk[k] for k in range(num_vans))
    solver.Minimize(obj)
    max_iter = 10
    van_path = {}
    for itr in range(max_iter):
        solver.Solve()
        print("Iteration: %d" % itr)
        print_solver(solver)
        van_path = find_all_path(num_vans)
        has_sub = add_constraint_subtour(van_path)
        if not has_sub:
            break
        print_all_subtour(van_path)

    print("\nMax ETA = %d" % max_eta.solution_value())
    # print_yk()
    # print_all_xk()
    # print_van_eta()
    print_path_eta(van_path)


if __name__ == '__main__':
    run()
