from ortools.linear_solver import pywraplp


def is_obj(tag):
    return tag in {"obj", "COST"}


def is_mark(var):
    return var in {"MARK", "MARKEND"}


def read_mps(filename, solver):
    with open(filename) as f:
        lhs_map = {}
        row_op = {}
        rhs_map = {}
        var_bnd = {}
        var_map = {}
        infinity = solver.Infinity()
        # lp
        for line in f:
            if line.startswith("ROWS"):
                break
        # rows
        for line in f:
            if line.startswith("COLUMNS"):
                break
            op, tag = line.strip().split()
            lhs_map[tag] = {}
            row_op[tag] = op
        # columns
        for line in f:
            if line.startswith("RHS"):
                break
            var, tag, val = line.strip().split()
            if is_mark(var):
                continue
            var_bnd[var] = {}
            lhs_map[tag][var] = float(val)
        # rhs
        for line in f:
            if line.startswith("RANGE"):
                continue
            if line.startswith("BOUNDS"):
                break
            _, tag, val = line.strip().split()
            rhs_map[tag] = (float(val))
        # bounds
        for line in f:
            if line.startswith("ENDATA"):
                break
            cols = line.strip().split()
            tag = cols[0]
            var = cols[2]
            if len(cols) == 4:
                bnd = float(cols[3])
                var_bnd[var][tag] = bnd
            else:
                var_bnd[var][tag] = True

        # variable
        for name, bnd in var_bnd.items():
            bv = bnd.get("BV", False)
            lb = bnd.get("LO", 0)
            ub = bnd.get("UP", infinity)
            # print("%s %f %f %s" % (name, lb, ub, bv))
            if bv:
                var_map[name] = solver.BoolVar(name)
            else:
                var_map[name] = solver.NumVar(lb, ub, name)

        # constraint
        for cname, variables in lhs_map.items():
            lhs = 0
            for name, a in variables.items():
                lhs += var_map[name] * a
            rhs = rhs_map.get(cname, 0)
            op = row_op[cname]
            # print("%s %s %f" % (cname, op, rhs))
            if op == "E":
                solver.Add(lhs == rhs, cname)
            elif op == "G":
                solver.Add(lhs >= rhs, cname)
            elif op == "L":
                solver.Add(lhs <= rhs, cname)
            elif op == "N":
                solver.Minimize(lhs)


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Optimal objective value = %f" % solver.Objective().Value())
    print("Problem solved in %f milliseconds" % solver.wall_time())


def run():
    filename = "../data/mps/gr4x6.mps"
    # filename = "../data/mps/bk4x3.mps"
    solver = pywraplp.Solver("mps",
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    read_mps(filename, solver)
    solver.Solve()
    print_solver(solver)


if __name__ == '__main__':
    run()
