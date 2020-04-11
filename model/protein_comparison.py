from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Objective value = %f" % solver.Objective().Value())
    print("Nodes = %d" % solver.nodes())
    print("Iterations = %d" % solver.iterations())


class Protein(object):
    def __init__(self, num, up):
        self.num = num
        self.up = up
        self.edges = up2set(up)

    def has_pair(self, i, j):
        return (i, j) in self.edges or (j, i) in self.edges


def up2set(up):
    myset = set()
    for i, ls in up.items():
        for j in ls:
            myset.add((i, j))
    return myset


def compare_protein(p1, p2):
    # Solver
    solver = pywraplp.Solver('protein_comparison',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    # Variables
    # Nodes
    xs = {}
    for i in range(p1.num):
        for j in range(p2.num):
            xs[(i, j)] = solver.BoolVar("x_%d_%d" % (i, j))
    # Edges
    ws = {}
    for e1 in p1.edges:
        for e2 in p2.edges:
            quad = (e1[0], e1[1], e2[0], e2[1])
            ws[(e1, e2)] = solver.NumVar(0, 1, "w_%d_%d_%d_%d" % quad)

    # Constraints
    # Nodes
    for i in range(p1.num):
        expr = sum(xs[(i, j)] for j in range(p2.num))
        solver.Add(expr <= 1)
    for j in range(p2.num):
        expr = sum(xs[(i, j)] for i in range(p1.num))
        solver.Add(expr <= 1)

    # Edges
    for (e1, e2), wv in ws.items():
        xij = xs[(e1[0], e2[0])]
        xkl = xs[(e1[1], e2[1])]
        solver.Add(wv <= xij)
        solver.Add(wv <= xkl)

    # # Crossover
    for i in range(p1.num):
        for j in range(p2.num):
            if (i, j) not in xs:
                continue
            for k in range(i + 1, p1.num):
                for l in range(j):
                    if (k, l) not in xs:
                        continue
                    expr = xs[(i, j)] + xs[(k, l)] <= 1
                    solver.Add(expr)

    # Object
    total = sum(wv for wv in ws.values())
    solver.Maximize(total)

    # Solve
    solver.Solve()
    print_solver(solver)

    def print_variable():
        for (ii, jj), xv in xs.items():
            v = xv.solution_value()
            if v > 0:
                print("node (%d, %d) %d" % (ii, jj, v))
        for (ee1, ee2), wwv in ws.items():
            v = wwv.solution_value()
            if v > 0:
                print("edge (%d, %d) (%d, %d) %.1f" % (ee1[0], ee1[1], ee2[0], ee2[1], v))

    print_variable()

    return solver


def run0():
    num1 = 8
    up1 = {
        0: [3, 5],
        1: [3],
        2: [5],
        3: [6],
        4: [7],
        5: [7],
    }
    num2 = 10
    up2 = {
        0: [2, 3],
        1: [2],
        2: [8],
        3: [6, 7],
        4: [9],
        5: [7],
        6: [9],
    }
    p1 = Protein(num1, up1)
    p2 = Protein(num2, up2)
    compare_protein(p1, p2)


def run1():
    num1 = 9
    up1 = {
        0: [1],
        1: [8],
        2: [3, 4],
        4: [5],
        5: [6],
        6: [8],
        7: [8],
    }
    num2 = 11
    up2 = {
        0: [3],
        1: [2],
        3: [5, 6],
        4: [5],
        5: [7],
        6: [7, 9],
        8: [9],
        9: [10],
    }
    p1 = Protein(num1, up1)
    p2 = Protein(num2, up2)
    compare_protein(p1, p2)


if __name__ == '__main__':
    run1()
