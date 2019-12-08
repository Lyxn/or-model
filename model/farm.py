from ortools.linear_solver import pywraplp

from util import util


def print_solver(solver):
    print('Number of variables = %d' % solver.NumVariables())
    print('Number of constraints = %d' % solver.NumConstraints())
    print("Optimal objective value = %f" % solver.Objective().Value())


def run():
    # Solver
    solver = pywraplp.Solver('farm_planning',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    infinity = solver.Infinity()

    # Context
    num_year = 5
    farm_acre = 200

    # cow
    heifer_age = 2
    max_age = 12
    num_cows = 120
    heifer_acre = 2 / 3
    cow_acre = 1
    calves_year = 1.1
    rate_bullock = 0.5
    price_bullock = 30
    price_heifer = 40
    price_cow_old = 120
    mortality_heifer = 0.05
    mortality_cow = 0.02
    revenue_cow = 370
    outlay_limit = 130
    cow_outlay = 200
    cow_grain = 0.6
    cow_beet = 0.7
    cow_lower = num_cows * 0.5
    cow_upper = num_cows * 1.75
    interest = 0.15
    cow_repay = cow_outlay * util.calc_compound_rate(interest, 10)
    # cow_repay = 39.71

    # sugar beet
    beet_yield = 1.5
    beet_buy_price = 70
    beet_sell_price = 58

    # grain
    grain_group = 4
    group_size = [20, 30, 20, 10]
    group_yield = [1.1, 0.9, 0.8, 0.65]
    grain_buy_price = 90
    grain_sell_price = 75

    # labour & cost
    item_labour = [10, 42, 4, 14]  # h
    item_cost = [50, 100, 15, 10]
    labour_cost_year = 4000
    label_unit = 120  # 100h
    labour_year = 55  # 100h

    # Variable
    x_grain = {}
    for i in range(grain_group):
        group_ub = group_yield[i] * group_size[i]
        for t in range(num_year):
            x_grain[(i, t)] = solver.NumVar(0, group_ub, "grain_%d_%d" % (i, t))

    y_beet = {}
    for t in range(num_year):
        y_beet[t] = solver.NumVar(0, infinity, "beet_%d" % t)

    grain_buy = {}
    grain_sell = {}
    beet_buy = {}
    beet_sell = {}
    for t in range(num_year):
        grain_buy[t] = solver.NumVar(0, infinity, "grain_buy_%d" % t)
        grain_sell[t] = solver.NumVar(0, infinity, "grain_sell_%d" % t)
        beet_buy[t] = solver.NumVar(0, infinity, "beet_buy_%d" % t)
        beet_sell[t] = solver.NumVar(0, infinity, "beet_sell_%d" % t)

    labour_extra = {}  # unit 100h
    m_outlay = {}  # unit 200
    heifer_sell = {}
    cow_age0 = {}
    for t in range(num_year):
        labour_extra[t] = solver.IntVar(0, infinity, "labour_extra_%d" % t)
        m_outlay[t] = solver.IntVar(0, cow_upper, "outlay_%d" % t)
        heifer_sell[t] = solver.IntVar(0, cow_upper, "heifer_sell_%d" % t)
        cow_age0[t] = solver.NumVar(0, cow_upper, "age_0_%d" % t)

    cow_age = {}
    for i in range(1, max_age + 1):
        for t in range(num_year):
            cow_age[(i, t)] = solver.NumVar(0, cow_upper, "age_%d_%d" % (i, t))

    profits = {}
    for t in range(num_year):
        profits[t] = solver.NumVar(0, infinity, "profit_%d" % t)

    # Constraint
    # the end of first year
    for i in range(1, max_age + 1):
        if i <= heifer_age:
            solver.Add(cow_age[(i, 0)] == 9.5)
        else:
            solver.Add(cow_age[(i, 0)] == 9.8)
    # continuity
    for t in range(1, num_year):
        solver.Add(cow_age[(1, t)] == cow_age0[t - 1] * 0.95)
        solver.Add(cow_age[(2, t)] == cow_age[(1, t - 1)] * 0.95)
        for j in range(3, max_age + 1):
            solver.Add(cow_age[(j, t)] == cow_age[(j - 1, t - 1)] * 0.98)

    for t in range(num_year):
        cows = sum(cow_age[(j, t)] for j in range(2, max_age))
        solver.Add(cow_age0[t] == 0.5 * calves_year * cows - heifer_sell[t])

    # accommodation
    for t in range(num_year):
        outlays = sum(m_outlay[k] for k in range(t + 1))
        cows = cow_age0[t] + sum(cow_age[(j, t)] for j in range(1, max_age))
        expr = cows <= outlay_limit + outlays
        solver.Add(expr)

    # grain & sugar beet consumption
    for t in range(num_year):
        cows = sum(cow_age[(j, t)] for j in range(2, max_age))
        grain = sum(x_grain[(i, t)] for i in range(grain_group))
        expr_grain = cows * cow_grain <= grain + grain_buy[t] - grain_sell[t]
        solver.Add(expr_grain)
        expr_beet = cows * cow_beet <= y_beet[t] + beet_buy[t] - beet_sell[t]
        solver.Add(expr_beet)

    # Acreage & Labour
    for t in range(num_year):
        heifer = cow_age0[t] + cow_age[(1, t)]
        cows = sum(cow_age[(j, t)] for j in range(2, max_age))
        grain = sum(x_grain[(i, t)] / group_yield[i] for i in range(grain_group))
        beet = y_beet[t] / beet_yield
        expr_acre = 2 / 3 * heifer + cows + grain + beet <= farm_acre
        solver.Add(expr_acre)
        expr_labour = 0.1 * heifer + 0.42 * cows + 0.04 * grain + 0.14 * beet <= labour_extra[t] + labour_year
        solver.Add(expr_labour)

    # End Total
    last = num_year - 1
    cow_end = sum(cow_age[(j, last)] for j in range(2, max_age))
    solver.Add(cow_end <= cow_upper)
    solver.Add(cow_end >= cow_lower)

    # Profit
    for t in range(num_year):
        cows = sum(cow_age[(j, t)] for j in range(2, max_age))
        # profit
        profit_bullock = cows * calves_year * rate_bullock * price_bullock
        profit_heifer = price_heifer * heifer_sell[t]
        profit_cow_old = price_cow_old * cow_age[(12, t)]
        profit_milk = revenue_cow * cows
        profit_grain = grain_sell[t] * grain_sell_price - grain_buy[t] * grain_buy_price
        profit_beet = beet_sell[t] * beet_sell_price - beet_buy[t] * beet_buy_price
        profit_year = profit_bullock + profit_heifer + profit_cow_old + profit_milk + profit_grain + profit_beet
        # cost
        cost_labour = labour_cost_year + labour_extra[t] * label_unit
        cost_heifer = 50 * (cow_age0[t] + cow_age[(1, t)])
        cost_cow = 100 * cows
        cost_grain = 15 * sum(x_grain[(i, t)] / group_yield[i] for i in range(grain_group))
        cost_beet = 10 * y_beet[t] / beet_yield
        cost_loan = cow_repay * sum(m_outlay[k] for k in range(t + 1))
        cost_year = cost_labour + cost_heifer + cost_cow + cost_grain + cost_beet + cost_loan
        solver.Add(profit_year - cost_year == profits[t])

    # Object
    profit_total = sum(profits[t] for t in range(num_year))
    loan_remain = cow_repay * sum(m_outlay[t] * (5 + t) for t in range(num_year))
    solver.Maximize(profit_total - loan_remain)

    # Solve
    solver.Solve()
    print_solver(solver)

    def print_solution(y):
        print("Year %d" % y)
        cows = sum(cow_age[(j, y)].solution_value() for j in range(2, max_age))
        print("Diary cow=%.2f" % cows)
        gp = [x_grain[(i, y)].solution_value() for i in range(grain_group)]
        grow = " ".join("%.2f" % x for x in gp)
        print("Grain sell=%.2f buy=%.2f grow=%s" % (grain_sell[y].solution_value(),
                                                    grain_buy[y].solution_value(),
                                                    grow))
        print("Beet sell=%.2f buy=%.2f grow=%.2f " % (beet_sell[y].solution_value(),
                                                      beet_buy[y].solution_value(),
                                                      y_beet[y].solution_value()))
        print("Sell heifers %d" % heifer_sell[y].solution_value())
        print("Profit %.2f" % profits[y].solution_value())

    for t in range(num_year):
        print_solution(t)


if __name__ == '__main__':
    run()
