from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Objective value = %f" % solver.Objective().Value())
    print("Nodes = %d" % solver.nodes())
    print("Iterations = %d" % solver.iterations())


def fold_protein(num_acids, hydrophobic_acids):
    # Solver
    solver = pywraplp.Solver('protein_folding',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    # Variable
    # Fold
    y = {}
    for i in range(2, num_acids - 1):
        y[i] = solver.BoolVar("y_%d" % i)
    # Match
    num_hydrophobic_acids = len(hydrophobic_acids)
    x = {}
    for i in range(num_hydrophobic_acids):
        idx = hydrophobic_acids[i]
        for j in range(i + 1, num_hydrophobic_acids):
            jdx = hydrophobic_acids[j]
            diff = jdx - idx
            if diff % 2 != 0 and diff > 2:
                x[(idx, jdx)] = solver.BoolVar("x_%d_%d" % (idx, jdx))

    # Constraint
    for i, j in x:
        mid = (i + j - 1) / 2
        for k in range(i, j):
            if k != mid:
                expr = x[(i, j)] + y[k] <= 1
            else:
                expr = x[(i, j)] == y[k]
            solver.Add(expr)

    # Object
    obj = sum(x[k] for k in x)
    solver.Maximize(obj)

    # Solve
    solver.Solve()
    print_solver(solver)

    def print_folding():
        fold_idx = []
        for cur in y:
            if y[cur].solution_value() != 0:
                print("fold", cur)
                fold_idx.append(cur)
        print_folds(num_acids, hydrophobic_acids, fold_idx)

    print_folding()

    return solver


def print_folds(num_acids, hydrophobic_acids, folds):
    str_nil = " "
    str_neg = "*"
    str_pos = "+"
    sep = "  "

    def print_fold(offset, beg_idx, end_idx, is_left):
        num_nil = offset - 1
        if is_left:
            num_nil = offset - (end_idx - beg_idx) - 1
        nils = [str_nil] * num_nil + [""]
        nils_str = sep.join(nils)
        acids = []
        for i in range(beg_idx, end_idx + 1):
            if i in hydrophobic_acids:
                acids.append(str_neg)
            else:
                acids.append(str_pos)
        if is_left:
            acids.reverse()
        print(nils_str + sep.join(acids))

    offset = calc_offset(num_acids, folds)
    is_left = 0
    last = 0
    for cur in folds:
        print_fold(offset, last + 1, cur, is_left)
        length = cur - last
        if is_left:
            offset -= length - 1
        else:
            offset += length - 1
        is_left = 1 - is_left
        last = cur
    print_fold(offset, last + 1, num_acids, is_left)


def calc_offset(num, folds):
    offset = 1
    min_offset = offset
    is_left = 0
    last = 0
    for cur in folds:
        length = cur - last
        if is_left:
            offset -= length - 1
        else:
            offset += length - 1
        is_left = 1 - is_left
        last = cur
        if min_offset > offset:
            min_offset = offset
    if is_left:
        length = num - last
        offset -= length - 1
    min_offset = 2 - min_offset if min_offset < 1 else 1
    return min_offset


def run0():
    # Context
    num_acids = 27
    hydrophobic_acids = [2, 3, 4, 6, 9,
                         11, 14, 16, 19, 22,
                         23, 26]
    # Optimal
    fold_protein(num_acids, hydrophobic_acids)
    # Reference
    folds = [7, 11, 17, 24]
    print_folds(num_acids, hydrophobic_acids, folds)


def run1():
    # Context
    num_acids = 50
    hydrophobic_acids = [2, 4, 5, 6, 11,
                         12, 17, 20, 21, 25,
                         27, 28, 30, 31, 33,
                         37, 44, 46]
    # Optimal
    fold_protein(num_acids, hydrophobic_acids)
    # Reference
    folds = [3, 8, 22, 35]
    print_folds(num_acids, hydrophobic_acids, folds)


if __name__ == '__main__':
    run0()
