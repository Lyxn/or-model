import math

from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Objective value = %f" % solver.Objective().Value())


def run():
    # Solver
    solver = pywraplp.Solver('milk_collection',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    # Context
    num_day = 2
    num_farms = 21
    num_everyday = 10
    idx_other = num_everyday
    farm_east = [0, -3, 1, 4, -5, -5, -4, 6, 3, -1, 0, 6, 2, -2, 6, 1, -3, -6, 2, -6, 5]
    farm_north = [0, 3, 11, 7, 9, -2, -7, 0, -6, -3, -6, 4, 5, 8, 10, 8, 1, 5, 9, -5, -4]
    farm_collection = [0, 5, 4, 3, 6, 7, 3, 4, 6, 5, 4, 7, 3, 4, 5, 6, 8, 5, 7, 6, 6]
    capacity = 80

    dist_map = {}

    def get_farm_dist(i, j):
        if (i, j) in dist_map:
            return dist_map[(i, j)]
        elif (j, i) in dist_map:
            return dist_map[(j, i)]
        src_east = farm_east[i]
        src_north = farm_north[i]
        dst_east = farm_east[j]
        dst_north = farm_north[j]
        diff_east = dst_east - src_east
        diff_north = dst_north - src_north
        dist = math.sqrt(diff_east * diff_east + diff_north * diff_north)
        dist_map[(i, j)] = dist
        return dist

    # Variable
    xk = {}
    for k in range(num_day):
        for i in range(num_farms):
            for j in range(i + 1, num_farms):
                xk[(k, i, j)] = solver.BoolVar("x_%d_%d_%d" % (k, i, j))
    yk = {}
    for k in range(num_day):
        for i in range(idx_other, num_farms):
            yk[(k, i)] = solver.BoolVar("y_%d_%d" % (k, i))

    # Constraint
    # collection
    capacity_extra = capacity - sum(farm_collection[i] for i in range(num_everyday))
    for k in range(num_day):
        lhs = sum(yk[(k, i)] * farm_collection[i] for i in range(idx_other, num_farms))
        solver.Add(lhs <= capacity_extra)
    # visit farms only once
    for i in range(idx_other, num_farms):
        expr = yk[(0, i)] + yk[(1, i)] == 1
        solver.Add(expr, "yk_%d" % i)

    # visit farm every day
    for k in range(num_day):
        for i in range(num_everyday):
            lhs = 0
            for j in range(num_farms):
                if j < i:
                    lhs += xk[(k, j, i)]
                elif i < j:
                    lhs += xk[(k, i, j)]
            solver.Add(lhs == 2, "everyday_%d_%d" % (k, i))

    # visit farm every other day
    for k in range(num_day):
        for i in range(idx_other, num_farms):
            lhs = - 2 * yk[(k, i)]
            for j in range(num_farms):
                if j < i:
                    lhs += xk[(k, j, i)]
                elif i < j:
                    lhs += xk[(k, i, j)]
            solver.Add(lhs == 0, "other_%d_%d" % (k, i))

    # yk upper
    def add_constraint_upper():
        for k in range(num_day):
            for i in range(idx_other, num_farms):
                for j in range(num_everyday):
                    solver.Add(xk[(k, j, i)] <= yk[(k, i)], "other1_%d_%d_%d" % (k, j, i))
                for j in range(i + 1, num_farms):
                    solver.Add(xk[(k, i, j)] <= yk[(k, i)], "other2_%d_%d_%d" % (k, i, j))
                    solver.Add(xk[(k, i, j)] <= yk[(k, j)], "other3_%d_%d_%d" % (k, i, j))

    # anchor
    solver.Add(yk[(0, idx_other)] == 1, "anchor")

    # Object
    obj = 0
    for i in range(num_farms):
        for j in range(i + 1, num_farms):
            obj += (xk[(0, i, j)] + xk[(1, i, j)]) * get_farm_dist(i, j)
    solver.Minimize(obj)

    def print_all_xk():
        for k in range(num_day):
            print("Day %d" % k)
            print_xk(k)

    def print_xk(k):
        for i in range(num_farms):
            out = "farm %02d:" % i
            for j in range(num_farms):
                c = "-"
                if i < j:
                    c = "%d" % xk[(k, i, j)].solution_value()
                elif i == j:
                    c = "+"
                out += "\t%s" % c
            print(out)

    def print_yk():
        for k in range(num_day):
            out = "Day %d:" % k
            for i in range(idx_other, num_farms):
                out += "\t%d" % yk[(k, i)].solution_value()
            print(out)

    def get_next(k, src, last):
        for f in range(num_farms):
            if f == src or f == last:
                continue
            v = xk[(k, src, f)] if src < f else xk[(k, f, src)]
            if v.solution_value() == 1:
                return f
        return -1

    def find_cycle(k):
        cycles = []
        visits = set()
        for src in range(num_farms):
            if src in visits:
                continue
            cycle = [src]
            last = -1
            cur = get_next(k, src, last)
            last = src
            if cur == -1:
                continue
            for itr in range(num_farms):
                if cur == src:
                    break
                visits.add(cur)
                cycle.append(cur)
                nxt = get_next(k, cur, last)
                last = cur
                cur = nxt
            cycles.append(cycle)
        return cycles

    def find_all_subtour():
        return dict((x, find_cycle(x)) for x in range(num_day))

    def add_day_subtour(k, subtour):
        num = len(subtour)
        lhs = 0
        for s in range(num - 1):
            for d in range(s + 1, num):
                src = subtour[s]
                dst = subtour[d]
                lhs += xk[(k, src, dst)] if src < dst else xk[(k, dst, src)]
        solver.Add(lhs <= num - 1)

    def add_constraint_subtour(k_subtour):
        has_subtour = False
        for k, subtours in k_subtour.items():
            if len(subtours) != 1:
                has_subtour = True
                for sub in subtours:
                    add_day_subtour(k, sub)
        return has_subtour

    def print_subtour(subtours):
        for cycle in subtours:
            print(cycle)

    def print_all_subtour(subtours):
        for k in range(num_day):
            print("Day %d" % k)
            print_subtour(subtours[k])

    def print_capacity(k_sub):
        for k, subs in k_subtour.items():
            print("Day %d" % k)
            for sub in subs:
                print([x + 1 for x in sub])
                cap = 0
                for f in sub:
                    cap += farm_collection[f]
                print("Collection %d" % cap)

    # Solve
    add_constraint_upper()
    max_iter = 10
    k_subtour = {}
    for itr in range(max_iter):
        solver.Solve()
        print("Iteration: %d" % itr)
        print_solver(solver)
        k_subtour = find_all_subtour()
        has_sub = add_constraint_subtour(k_subtour)
        if not has_sub:
            break
        print_all_subtour(k_subtour)

    print("\nOptimal Dist %f" % solver.Objective().Value())
    print_capacity(k_subtour)


if __name__ == '__main__':
    run()
