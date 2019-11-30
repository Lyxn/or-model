import sys
import time

from ortools.graph.pywrapgraph import SimpleMinCostFlow


def read_network(filename):
    nwk = SimpleMinCostFlow()
    with open(filename) as f:
        # obj
        for line in f:
            if line.startswith("ROWS"):
                break
        # node
        for line in f:
            if line.startswith("COLUMNS"):
                break
            _, tag = line.strip().split()
            if tag == "obj":
                continue
            node = int(tag[1:])
            nwk.SetNodeSupply(node, 0)
        # arc
        cost = 0
        head = 0
        tail = 0
        cur_arc = ""
        arc_data = {}
        for line in f:
            if line.startswith("RHS"):
                arc_data[cur_arc] = (tail, head, cost)
                break
            arc, tag, val = line.strip().split()
            if arc != cur_arc:
                arc_data[cur_arc] = (tail, head, cost)
                cur_arc = arc
                cost = 0
                head = 0
                tail = 0
            if tag == "obj":
                cost = int(float(val))
            elif val == "1":
                tail = int(tag[1:])
            elif val == "-1":
                head = int(tag[1:])
        # supply
        for line in f:
            if line.startswith("RANGES"):
                break
            _, tag, val = line.strip().split()
            node = int(tag[1:])
            supply = int(float(val))
            nwk.SetNodeSupply(node, supply)
        # range
        for line in f:
            if line.startswith("BOUNDS"):
                break
        # arc capacity
        for line in f:
            if line.startswith("ENDATA"):
                break
            _, _, arc, val = line.strip().split()
            tail, head, cost = arc_data[arc]
            capacity = int(float(val))
            aid = nwk.AddArcWithCapacityAndUnitCost(tail, head, capacity, cost)
            # sys.stderr.write("%d %s %d %d %d %d\n" % (aid, arc, tail, head, capacity, cost))
    return nwk


def print_flow(nwk):
    for i in range(nwk.NumArcs()):
        flow = nwk.Flow(i)
        if flow > 0:
            line = "%d %d %d %d %d %d" % (i,
                                          nwk.Tail(i),
                                          nwk.Head(i),
                                          nwk.Capacity(i),
                                          nwk.UnitCost(i),
                                          flow)
            sys.stderr.write(line + "\n")


def run():
    filename = "./data/mps/16_n14.mps"
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
