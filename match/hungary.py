import numpy as np


def hungary(w):
    n = len(w)
    dx = np.zeros(n)
    dy = np.zeros(n)
    for i in range(n):
        dx[i] = max(w[i])

    ym = np.zeros(n, dtype=int) - 1
    row = set()
    col = set()
    max_num = 1e10

    def augment(x):
        row.add(x)
        for y in range(n):
            if y in col:
                continue
            t = dx[x] + dy[y] - w[x][y]
            if t == 0:
                col.add(y)
                if ym[y] == -1 or augment(ym[y]):
                    ym[y] = x
                    return True
        return False

    def find_delta():
        d = max_num
        for s in row:
            for t in range(n):
                if t in col:
                    continue
                d = min(dx[s] + dy[t] - w[s][t], d)
        return d

    for xx in range(n):
        while True:
            row.clear()
            col.clear()
            if augment(xx):
                break
            # print((dx - w.T).T + dy)
            delta = find_delta()
            for i in row:
                dx[i] -= delta
            for j in col:
                dy[j] += delta
    return ym


def test():
    n = 10
    cost = np.random.randint(3, 10, size=(n, n))
    # cost = np.array([
    #     [2, 3, 4, 5],
    #     [3, 5, 5, 6],
    #     [8, 7, 10, 12],
    #     [0, 0, 0, 0],
    # ])
    n = len(cost)
    print(cost)
    ym = hungary(cost)
    print(ym)
    total = sum(cost[ym[i]][i] for i in range(n))
    print("Total ", total)


if __name__ == '__main__':
    test()
