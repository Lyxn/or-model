import numpy as np
import osqp
from scipy import sparse


def run():
    product_name = ["milk", "butter", "cheese1", "cheese2"]
    num_product = len(product_name)
    compositions = [
        [4, 9, 87],
        [80, 2, 18],
        [35, 30, 35],
        [25, 40, 35],
    ]
    last_demand = [4820, 320, 210, 70]
    last_price = [0.297, 0.720, 1.050, 0.815]
    elasticities = [0.4, 2.7, 1.1, 0.4]
    cross_elasticities = [0.1, 0.4]

    def get_price_ratio(p, idx):
        return (p - last_price[idx]) / last_price[idx]

    def get_demand_by_price(p, idx):
        ratio = get_price_ratio(p, idx) * elasticities[idx]
        return last_demand[idx] * (1 - ratio)

    def get_demand_milk(p):
        return get_demand_by_price(p, 0)

    def get_demand_butter(p):
        return get_demand_by_price(p, 1)

    def get_demand_cheese1(p1, p2):
        idx = 2
        ratio = get_price_ratio(p1, idx) * elasticities[idx] \
                - get_price_ratio(p2, 3) * cross_elasticities[0]
        return last_demand[idx] * (1 - ratio)

    def get_demand_cheese2(p1, p2):
        idx = 3
        ratio = get_price_ratio(p2, idx) * elasticities[idx] \
                - get_price_ratio(p1, 2) * cross_elasticities[1]
        return last_demand[idx] * (1 - ratio)

    def get_demands(prices):
        return [
            get_demand_milk(prices[0]),
            get_demand_butter(prices[1]),
            get_demand_cheese1(prices[2], prices[3]),
            get_demand_cheese2(prices[2], prices[3]),
        ]

    def print_result():
        print("Product", *product_name, sep="\t")
        p_out = ["%.4f" % x for x in price_opt]
        print("Price ", *p_out, sep="\t")
        d_out = ["%.2f" % x for x in demand_opt]
        print("Demand", *d_out, sep="\t")
        total = sum(price_opt[i] * demand_opt[i] for i in range(num_product))
        print("Total = %f" % total)

    price_opt = solve_qp()
    demand_opt = get_demands(price_opt)
    print_result()


def solve_qp():
    p_mat = sparse.csc_matrix([
        [-6492, 0, 0, 0],
        [0, -1200, 0, 0],
        [0, 0, -220, 26.5],
        [0, 0, 26.5, -34],
    ])
    p_mat = -2 * p_mat
    p_vec = -np.array([6748, 1184, 420, 70])
    a_mat = sparse.csc_matrix([
        [260, 960, 70.25, -0.6],
        [584, 24, 55.2, 5.8],
        [4.82, 0.32, 0.21, 0.07],
        [0, 0, 220, -26],
        [0, 0, -27, 34],
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ])
    eps = 0
    lb = np.array([782, 35, eps, -np.inf, -np.inf, eps, eps, eps, eps])
    ub = np.array([np.inf, np.inf, 1.939, 420, 70, 1.039, 0.987, np.inf, np.inf])

    prob = osqp.OSQP()
    prob.setup(p_mat, p_vec, a_mat, lb, ub)
    res = prob.solve()
    return res.x


if __name__ == '__main__':
    run()
