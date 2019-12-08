from ortools.linear_solver import pywraplp


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Optimal objective value = %f" % solver.Objective().Value())


def run():
    # Solver
    solver = pywraplp.Solver('farm_planning',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    # Context
    num_cities = 3
    num_departments = 5
    city_names = ["Bristol", "Brighton", "London"]

    quantities = [[0, 1.0, 1.5, 0], [1.4, 1.2, 0], [0, 2.0], [0.7]]
    costs = [[5, 14, 13], [5, 9], [10]]

    def get_quantity(a, b):
        return quantities[a][b - a - 1]

    def get_cost(a, b):
        if a > b:
            a, b = b, a
        return costs[a][b - a]

    # Variable
    xv = {}
    yv = {}
    # location
    for i in range(num_cities):
        for j in range(num_departments):
            xv[(i, j)] = solver.BoolVar("x_%d_%d" % (i, j))

    # Constraint
    # department
    for j in range(num_departments):
        expr = sum(xv[(i, j)] for i in range(num_cities)) == 1
        solver.Add(expr)
    # city
    for i in range(num_cities - 1):
        num = sum(xv[(i, j)] for j in range(num_departments))
        solver.Add(num <= 3)
    num_london = sum(xv[(2, j)] for j in range(num_departments))
    solver.Add(num_london <= 1)

    # Object
    total_cost = 0
    for i in range(num_cities):
        for j in range(num_departments - 1):
            for k in range(num_cities):
                for l in range(j + 1, num_departments):
                    quant = get_quantity(j, l)
                    cost = get_cost(i, k)
                    if quant == 0.0:
                        continue
                    var = solver.BoolVar("y_%d_%d_%d_%d" % (i, k, j, l))
                    expr = var >= xv[(i, j)] + xv[(k, l)] - 1
                    solver.Add(expr)
                    solver.Add(var <= xv[(i, j)])
                    solver.Add(var <= xv[(k, l)])
                    total_cost += var * quant * cost
                    yv[(i, j, k, l)] = var
    solver.Minimize(total_cost)
    solver.Solve()
    print_solver(solver)

    def print_location():
        for i in range(num_cities):
            out = "%s: " % city_names[i]
            for j in range(num_departments):
                out += "\t%d" % xv[(i, j)].solution_value()
            print(out)

    print_location()


if __name__ == '__main__':
    run()
