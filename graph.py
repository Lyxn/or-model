import sys
import time

from ortools.graph.pywrapgraph import SimpleMinCostFlow


def parse_node(nd_str):
    cols = nd_str.split(",")
    if len(cols) == 2:
        node = int(cols[0])
        supply = int(cols[1])
    else:
        node = int(nd_str)
        supply = 0
    return node, supply


def parse_arc(arc_str):
    cols = arc_str.split(",")
    dst = int(cols[0])
    if len(cols) == 3:
        cost = int(cols[1])
        cap = int(cols[2])
    else:
        cost = int(cols[1])
        cap = 100000000000
    return dst, cap, cost


def read_network(filename):
    nwk = SimpleMinCostFlow()
    with open(filename) as f:
        first = f.readline()
        num_node = int(first)
        for line in f:
            nd_str, arc_list = line.strip().split(":")
            node, supply = parse_node(nd_str)
            nwk.SetNodeSupply(node, supply)
            for arc_info in arc_list.split(";"):
                if len(arc_info.strip()) == 0:
                    continue
                dst, cap, cost = parse_arc(arc_info)
                nwk.AddArcWithCapacityAndUnitCost(node, dst, cap, cost)
    return nwk


def run():
    if len(sys.argv) < 2:
        print("USAGE: python %s $FILE" % sys.argv[0])
        return
    filename = sys.argv[1]
    start = time.time()
    nwk = read_network(filename)
    print("Network time=%f" % (time.time() - start))
    print("Network NumNode=%d NumArc=%s" % (nwk.NumNodes(), nwk.NumArcs()))
    start = time.time()
    nwk.Solve()
    print("Solve time=%f" % (time.time() - start))
    print("Optimal %s" % nwk.OptimalCost())


if __name__ == '__main__':
    run()
