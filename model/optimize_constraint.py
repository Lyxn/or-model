from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Optimal objective value = %f" % solver.Objective().Value())


def print_constraint(coefficients, rhs, fmt=lambda x: "%d" % x):
    idx = 0
    expr = "%s*x%d" % (fmt(coefficients[idx]), idx + 1)
    for i in range(1, len(coefficients)):
        a = coefficients[i]
        if a > 0:
            expr += " + %s*x%d" % (fmt(a), i + 1)
        elif a < 0:
            expr += " - %s*x%d" % (fmt(-a), i + 1)
    expr += " <= %s" % fmt(rhs)
    print(expr)


def argsort(s):
    return sorted(range(len(s)), key=lambda k: s[k], reverse=True)


def get_rev_idx(idxs):
    num = len(idxs)
    rev = [0] * num
    for i in range(num):
        rev[idxs[i]] = i
    return rev


# TODO methods to get ceilings and roofs
def run():
    rhs = 37
    coefficients = [9, 13, -14, 17, 13, -19, 23, 21]
    num = len(coefficients)
    print_constraint(coefficients, rhs)
    sign = [1 if x > 1 else -1 for x in coefficients]
    rhs_new = rhs - sum(x for x in coefficients if x < 0)
    coef_new = [abs(x) for x in coefficients]
    idxs = argsort(coef_new)
    coef_sort = [coef_new[i] for i in idxs]
    rev_idxs = get_rev_idx(idxs)
    print_constraint(coef_sort, rhs_new)

    def recover_constraint(arr, a0):
        coef_rev = [arr[i] for i in rev_idxs]
        coef_rev = [coef_rev[i] * sign[i] for i in range(num)]
        rhs_rev = a0 + sum(x for x in coef_rev if x < 0)
        return coef_rev, rhs_rev

    ceilings = [{1, 2, 3}, {1, 2, 4, 8}, {1, 2, 6, 7}, {1, 3, 5, 6}, {2, 3, 4, 6}, {2, 5, 6, 7, 8}]
    roofs = [{1, 2, 3, 8}, {1, 2, 5, 7}, {1, 3, 4, 7}, {1, 5, 6, 7, 8}, {2, 3, 4, 5}, {3, 4, 6, 7, 8}]
    coef_opt, rhs_opt = optimize_constraint(num, ceilings, roofs, rhs_new)
    coef_rev, rhs_rev = recover_constraint(coef_opt, rhs_opt)
    print_constraint(coef_opt, rhs_opt)
    print_constraint(coef_rev, rhs_rev)


def optimize_constraint(num_var, ceilings, roofs, upper):
    # Solver
    solver = pywraplp.Solver('optimize_constraint',
                             pywraplp.Solver.CLP_LINEAR_PROGRAMMING)

    # Variable
    num_var += 1
    a = {}
    for i in range(num_var):
        a[i] = solver.NumVar(0, upper, "a_%d" % i)

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
    # print_variable()
    rhs = a[0].solution_value()
    coef = [a[i].solution_value() for i in range(1, num_var)]
    return coef, rhs


if __name__ == '__main__':
    run()
