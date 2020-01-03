import time


def is_ceiling(a, a0, sub):
    num_coef = len(a)
    # condition i
    s = sum(a[t] for t in sub)
    if s > a0:
        return False
    # condition ii
    for t in range(num_coef):
        if t not in sub and s + a[t] < a0 + 1:
            return False
    # condition iii
    for t in range(num_coef):
        if t in sub:
            continue
        t1 = t + 1
        if t1 < num_coef and t1 in sub:
            if s + a[t] - a[t1] < a0 + 1:
                return False
    return True


def is_roof(a, a0, sub):
    num_coef = len(a)
    # condition i
    s = sum(a[t] for t in sub)
    if s < a0 + 1:
        return False
    # condition ii
    for t in sub:
        if s - a[t] > a0:
            return False
    # condition iii
    for t in sub:
        t1 = t + 1
        if t1 < num_coef and t1 not in sub:
            if s - a[t] + a[t1] > a0:
                return False
    return True


def find_roofs(a, a0):
    num_coef = len(a)
    roofs = []
    sub = [0]
    while True:
        num_sub = len(sub)
        if is_roof(a, a0, sub):
            roofs.append(sub)
        total = sum(a[j] for j in sub)
        sr = sub[-1]
        if sr < num_coef - 1:
            if total <= a0:
                sub = sub + [sr + 1]
            elif total > a0:
                sub = sub[:-1] + [sr + 1]
        else:
            has_next = False
            for t in range(num_sub - 2, -1, -1):
                if sub[t + 1] - sub[t] >= 2:
                    has_next = True
                    sub = sub[:t] + [sub[t] + 1]
                    break
            if not has_next:
                break
    return roofs


def find_ceilings(a, a0):
    num_coef = len(a)
    dual_a0 = sum(a) - a0 - 1
    roofs = find_roofs(a, dual_a0)

    def get_reverse(sub):
        return [x for x in range(num_coef) if x not in sub]

    return [get_reverse(roof) for roof in roofs]


def test0():
    a = [9, 7, 6, 6, 4]
    a0 = 12
    sub_list = [{0}, {1, 4}, {2, 3}]
    for sub in sub_list:
        print(is_ceiling(a, a0, sub))
    sub_list = [{0, 4}, {1, 3}, {2, 3, 4}]
    for sub in sub_list:
        print(is_roof(a, a0, sub))


def test1():
    a = [9, 7, 6, 6, 4]
    a0 = 12
    roofs = find_roofs(a, a0)
    print(roofs)
    ceilings = find_ceilings(a, a0)
    print(ceilings)


def test2():
    a0 = 70
    a = [23, 21, 19, 17, 14, 13, 13, 9]
    roofs = find_roofs(a, a0)
    print(roofs)
    ceilings = find_ceilings(a, a0)
    print(ceilings)


if __name__ == '__main__':
    start = time.time()
    test2()
    time_cost = time.time() - start
    print("time cost %f" % time_cost)
