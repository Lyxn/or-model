from ortools.linear_solver import pywraplp

from util import reduce


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Optimal objective value = %f" % solver.Objective().Value())


def print_constraint(coefficients, rhs, fmt=lambda x: "%d" % x):
    idx = 0
    expr = "%s*x%d" % (fmt(coefficients[idx]), idx + 1)
    for i in range(1, len(coefficients)):
        a = coefficients[i]
        if a >= 0:
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


def optimize_constraint(coefficients, rhs):
    num = len(coefficients)
    sign = [1 if x > 1 else -1 for x in coefficients]
    rhs_new = rhs - sum(x for x in coefficients if x < 0)
    coef_new = [abs(x) for x in coefficients]
    idxs = argsort(coef_new)
    coef_sort = [coef_new[i] for i in idxs]
    rev_idxs = get_rev_idx(idxs)

    def recover_constraint(arr, a0):
        coef_rev = [arr[i] for i in rev_idxs]
        coef_rev = [coef_rev[i] * sign[i] for i in range(num)]
        rhs_rev = a0 + sum(x for x in coef_rev if x < 0)
        return coef_rev, rhs_rev

    coef_opt, rhs_opt = reduce_coef(coef_sort, rhs_new)
    coef_opt_rev, rhs_opt_rev = recover_constraint(coef_opt, rhs_opt)
    print("positive ordered inequality")
    print_constraint(coef_sort, rhs_new)
    print_constraint(coef_opt, rhs_opt)
    return coef_opt_rev, rhs_opt_rev


def reduce_coef(a, a0):
    ceilings = reduce.find_ceilings(a, a0)
    roofs = reduce.find_roofs(a, a0)
    return solve_reduce_prob(len(a), ceilings, roofs, a0)


def solve_reduce_prob(num_var, ceilings, roofs, upper):
    # Solver
    solver = pywraplp.Solver('optimize_constraint',
                             pywraplp.Solver.CLP_LINEAR_PROGRAMMING)

    # Variable
    b = {}
    for i in range(num_var):
        b[i] = solver.NumVar(0, upper, "b_%d" % i)
    b0 = solver.NumVar(0, upper, "b0")

    # Constraint
    for i in range(num_var - 1):
        solver.Add(b[i] >= b[i + 1])

    # ceilings
    for ceiling in ceilings:
        expr = sum(b[i] for i in ceiling) <= b0
        solver.Add(expr)
    # roofs
    for roof in roofs:
        expr = sum(b[i] for i in roof) >= b0 + 1
        solver.Add(expr)

    # Object
    obj = sum(b[i] for i in range(num_var))
    solver.Minimize(obj)

    # Solve
    def print_variable():
        out_b0 = "b0:\t%d" % b0.solution_value()
        print(out_b0)
        out_bi = "bi:"
        for i in range(num_var):
            out_bi += "\t%d" % b[i].solution_value()
        print(out_bi)

    solver.Solve()
    # print_solver(solver)
    # print_variable()
    rhs = b0.solution_value()
    coef = [b[i].solution_value() for i in range(num_var)]
    return coef, rhs


def run():
    rhs = 37
    coefficients = [9, 13, -14, 17, 13, -19, 23, 21]
    # ceilings = [{1, 2, 3}, {1, 2, 4, 8}, {1, 2, 6, 7}, {1, 3, 5, 6}, {2, 3, 4, 6}, {2, 5, 6, 7, 8}]
    # roofs = [{1, 2, 3, 8}, {1, 2, 5, 7}, {1, 3, 4, 7}, {1, 5, 6, 7, 8}, {2, 3, 4, 5}, {3, 4, 6, 7, 8}]
    coef_opt, rhs_opt = optimize_constraint(coefficients, rhs)
    print_constraint(coefficients, rhs)
    print_constraint(coef_opt, rhs_opt)


def run1():
    a0_list = [80, 96, 20, 36, 44, 48, 24]
    ai_list = [
        [8, 12, 13, 64, 22, 41],
        [8, 12, 13, 75, 22, 41],
        [3, 6, 4, 18, 6, 4],
        [5, 10, 8, 32, 6, 12],
        [5, 13, 8, 42, 6, 20],
        [5, 13, 8, 48, 6, 20],
        [3, 2, 4, 8, 8, 4],
    ]
    num_ieq = len(a0_list)
    for i in range(num_ieq):
        a0 = a0_list[i]
        ai = ai_list[i]
        print("inequality %s" % i)
        bi, b0 = optimize_constraint(ai, a0)
        print_constraint(ai, a0)
        print_constraint(bi, b0)


if __name__ == '__main__':
    run1()
