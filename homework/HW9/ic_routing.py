"""Problem 5 - Wire routing in IC design (grid / maze routing).

The chip is modelled as a grid (one metal layer).  '#' cells are blocked (macros,
already-placed cells), every net is a pair of pins that must be joined by a wire of
grid cells, and two different nets may not use the same cell (they would short).

Part A - routing ONE net, five search methods
    1. Lee algorithm            BFS wave expansion, always shortest
    2. Hadlock algorithm        0-1 BFS on the "detour number", always shortest
    3. Soukup algorithm         target-directed DFS + BFS fallback, fast, not always shortest
    4. A*                       g + Manhattan h, always shortest
    5. A* with bend penalty     state = (cell, direction); every bend (= a via in a
                                real two-layer router) costs extra -> fewer bends

Part B - routing MANY nets
    * sequential routing, nets in the given order
    * sequential routing, shortest nets first (net-ordering heuristic)
    * rip-up and reroute: if a net cannot be routed, route it *through* the nets in its
      way (with a penalty), rip those nets up and put them back in the queue; cells that
      were fought over get a growing "history" cost so the nets learn to avoid them
      (the idea behind negotiation-based routers such as PathFinder).
"""
import heapq
import random
import time
from collections import deque

DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]


# ---------------------------------------------------------------- grid helpers
class Grid:
    def __init__(self, rows, cols, blocked=()):
        self.rows, self.cols = rows, cols
        self.blocked = set(blocked)

    @classmethod
    def from_text(cls, text):
        lines = text.splitlines()
        blocked = {(r, c) for r, line in enumerate(lines) for c, ch in enumerate(line) if ch == "#"}
        return cls(len(lines), len(lines[0]), blocked)

    def neighbours(self, cell, forbidden=frozenset()):
        r, c = cell
        for dr, dc in DIRS:
            n = (r + dr, c + dc)
            if (0 <= n[0] < self.rows and 0 <= n[1] < self.cols
                    and n not in self.blocked and n not in forbidden):
                yield n


def md(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def backtrace(parent, t):
    if t not in parent:
        return None
    path = []
    while t is not None:
        path.append(t)
        t = parent[t]
    return path[::-1]


def bends(path):
    if not path or len(path) < 3:
        return 0
    count = 0
    for a, b, c in zip(path, path[1:], path[2:]):
        if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
            count += 1
    return count


# ---------------------------------------------------- Part A: single-net routers
def lee(grid, s, t, forbidden=frozenset(), trace=None):
    """Lee (1961): wave expansion = BFS from the source, then backtrace.
    (All five single-net routers add their expanded cells to `trace` if it is a set.)"""
    parent = {s: None}
    q = deque([s])
    expanded = 0
    while q:
        cell = q.popleft()
        expanded += 1
        if trace is not None:
            trace.add(cell)
        if cell == t:
            break
        for n in grid.neighbours(cell, forbidden):
            if n not in parent:
                parent[n] = cell
                q.append(n)
    return backtrace(parent, t), expanded


def hadlock(grid, s, t, forbidden=frozenset(), trace=None):
    """Hadlock (1977): a step towards t costs 0, a step away costs 1 (one 'detour').
    0-1 BFS minimises detours d, and wire length = md(s, t) + 2d, so it is shortest."""
    detour = {s: 0}
    parent = {s: None}
    dq = deque([s])
    done = set()
    while dq:
        cell = dq.popleft()
        if cell in done:
            continue
        done.add(cell)
        if cell == t:
            break
        for n in grid.neighbours(cell, forbidden):
            w = 0 if md(n, t) < md(cell, t) else 1
            nd = detour[cell] + w
            if nd < detour.get(n, float("inf")):
                detour[n] = nd
                parent[n] = cell
                (dq.appendleft if w == 0 else dq.append)(n)
    if trace is not None:
        trace.update(done)
    return backtrace(parent, t), len(done)


def soukup(grid, s, t, forbidden=frozenset(), trace=None):
    """Soukup (1978): neighbours that move towards t go to the FRONT of the queue (DFS
    straight at the target); others go to the back (BFS when blocked).  A cell is
    labelled when first seen, so the path found is not always the shortest."""
    parent = {s: None}
    dq = deque([s])
    expanded = 0
    while dq:
        cell = dq.popleft()
        expanded += 1
        if trace is not None:
            trace.add(cell)
        if cell == t:
            break
        for n in grid.neighbours(cell, forbidden):
            if n not in parent:
                parent[n] = cell
                if md(n, t) < md(cell, t):
                    dq.appendleft(n)
                else:
                    dq.append(n)
    return backtrace(parent, t), expanded


def astar(grid, s, t, forbidden=frozenset(), cell_cost=None, trace=None):
    """A*: f = g + h with h = Manhattan distance (admissible because every step >= 1).
    cell_cost(cell) is an optional extra cost for entering a cell (used by rip-up)."""
    g = {s: 0}
    parent = {s: None}
    heap = [(md(s, t), 0, s)]
    closed = set()
    while heap:
        _, gc, cell = heapq.heappop(heap)
        if cell in closed:
            continue
        closed.add(cell)
        if cell == t:
            break
        for n in grid.neighbours(cell, forbidden):
            ng = gc + 1 + (cell_cost(n) if cell_cost else 0)
            if ng < g.get(n, float("inf")):
                g[n] = ng
                parent[n] = cell
                heapq.heappush(heap, (ng + md(n, t), ng, n))
    if trace is not None:
        trace.update(closed)
    return backtrace(parent, t), len(closed)


def astar_bends(grid, s, t, forbidden=frozenset(), bend_cost=5, trace=None):
    """A* over states (cell, direction). Each step costs 1, each change of direction
    costs bend_cost extra.  Minimises  length + bend_cost * bends."""
    start = (s, None)
    g = {start: 0}
    parent = {start: None}
    heap = [(md(s, t), 0, s, None)]
    closed = set()
    goal_state = None
    while heap:
        _, gc, cell, d = heapq.heappop(heap)
        state = (cell, d)
        if state in closed:
            continue
        closed.add(state)
        if cell == t:
            goal_state = state
            break
        for n in grid.neighbours(cell, forbidden):
            nd = (n[0] - cell[0], n[1] - cell[1])
            ng = gc + 1 + (bend_cost if d is not None and nd != d else 0)
            ns = (n, nd)
            if ng < g.get(ns, float("inf")):
                g[ns] = ng
                parent[ns] = state
                heapq.heappush(heap, (ng + md(n, t), ng, n, nd))
    if trace is not None:
        trace.update(cell for cell, _ in closed)
    if goal_state is None:
        return None, len(closed)
    path, st = [], goal_state
    while st is not None:
        path.append(st[0])
        st = parent[st]
    return path[::-1], len(closed)


SINGLE_NET_METHODS = [
    ("Lee (BFS)", lee),
    ("Hadlock (0-1 BFS)", hadlock),
    ("Soukup (DFS+BFS)", soukup),
    ("A* (Manhattan)", astar),
    ("A* + bend penalty", astar_bends),
]


# ------------------------------------------------------- Part B: multi-net routing
def route_sequential(grid, nets, order):
    """Route nets one by one; each finished wire becomes an obstacle for the rest."""
    all_pins = {p for pins in nets.values() for p in pins}
    used = set()
    routes = {}
    for name in order:
        s, t = nets[name]
        forbidden = (all_pins - {s, t}) | used
        path, _ = astar(grid, s, t, frozenset(forbidden))
        if path:
            routes[name] = path
            used |= set(path)
    return routes


def route_ripup(grid, nets, order, max_iterations=300, conflict_penalty=5, log=None):
    """Rip-up and reroute with history cost.
    Returns (best_routes, iterations_used) where best_routes is the legal state with the
    most routed nets seen during the search (ties: shorter total wire)."""
    all_pins = {p for pins in nets.values() for p in pins}
    owner = {}                      # cell -> net currently using it
    routes = {}
    history = {}                    # cell -> how many times nets fought over it
    queue = deque(order)
    best = {}
    it = 0
    while queue and it < max_iterations:
        it += 1
        name = queue.popleft()
        s, t = nets[name]
        pins_of_others = frozenset(all_pins - {s, t})

        def hist(c):
            return history.get(c, 0)

        # 1) try to route legally: other nets' wires are obstacles
        others = frozenset(c for c, n in owner.items() if n != name)
        path, _ = astar(grid, s, t, pins_of_others | others, cell_cost=hist)
        if path is None:
            # 2) allow crossing other wires at a penalty (never pins or macros)
            def cost(c):
                return hist(c) + (conflict_penalty if c in owner else 0)
            path, _ = astar(grid, s, t, pins_of_others, cell_cost=cost)
            if path is None:
                continue                          # sealed off by macros/pins: impossible
            conflict_cells = [c for c in path if c in owner]
            victims = {owner[c] for c in conflict_cells}
            for c in conflict_cells:              # remember the fight
                history[c] = history.get(c, 0) + 1
            for v in sorted(victims):             # rip up the nets in the way
                for c in routes.pop(v):
                    del owner[c]
                queue.append(v)                   # ...and reroute them later
        else:
            victims = set()
        routes[name] = path
        for c in path:
            owner[c] = name
        if log is not None:                       # (net routed, nets ripped up, state)
            log.append((name, sorted(victims), dict(routes)))
        if (len(routes), -total_length(routes)) > (len(best), -total_length(best)):
            best = dict(routes)
    return best, it


def total_length(routes):
    return sum(len(p) - 1 for p in routes.values())


def check_routes(grid, nets, routes):
    """Verify: every wire is connected, joins its own pins, avoids macros and other nets."""
    seen = {}
    for name, path in routes.items():
        s, t = nets[name]
        assert path[0] == s and path[-1] == t, name
        for a, b in zip(path, path[1:]):
            assert md(a, b) == 1, name
        for c in path:
            assert c not in grid.blocked, name
            assert c not in seen, f"short between {name} and {seen[c]}"
            seen[c] = name
    return True


def draw(grid, nets, routes):
    g = [["#" if (r, c) in grid.blocked else "." for c in range(grid.cols)] for r in range(grid.rows)]
    for name, path in routes.items():
        for r, c in path:
            g[r][c] = name.lower()
    for name, (s, t) in nets.items():
        for r, c in (s, t):
            g[r][c] = name.upper()
    return "\n".join("".join(row) for row in g)


def random_instance(seed, rows=12, cols=12, n_nets=6, n_blocks=4):
    rng = random.Random(seed)
    blocked = set()
    for _ in range(n_blocks):
        r, c = rng.randrange(rows - 2), rng.randrange(cols - 2)
        h, w = rng.randint(1, 3), rng.randint(1, 3)
        blocked |= {(r + i, c + j) for i in range(h) for j in range(w)
                    if r + i < rows and c + j < cols}
    grid = Grid(rows, cols, blocked)
    free = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in blocked]
    rng.shuffle(free)
    nets = {chr(ord("A") + k): (free[2 * k], free[2 * k + 1]) for k in range(n_nets)}
    return grid, nets


# -------------------------------------------------------------------------- demos
# chip 2 was picked by a small random search (seed 23) for a layout where the macros
# block every monotone path and Soukup's answer is not the shortest
BLOCKED_CHIP = """\
....................
...............#....
...............#....
...............#....
..#####......#####..
....##.......#####..
....##.......#####..
....##.......#####..
....##.......#......
....##.......##.....
....##.......#......
...................."""

OPEN_CHIP = """\
....................
..####.....#####....
..####.....#####....
..####..............
.........####.......
.........####..###..
.###.....####..###..
.###...........###..
.###..######........
......######........"""

MULTI_NET_NETS = {
    "A": ((3, 0), (3, 11)),     # long net across the chip
    "B": ((2, 4), (4, 4)),      # two short nets whose pins sit on A's straight path
    "C": ((2, 8), (4, 8)),
}


def compare_single_net(title, chip_text, s, t, show):
    grid = Grid.from_text(chip_text)
    print(f"--- Part A, {title}: one net from {s} to {t} ---")
    print(f"{'method':<20}{'length':>7}{'bends':>7}{'expanded':>10}{'time(ms)':>10}")
    paths = {}
    for name, fn in SINGLE_NET_METHODS:
        t0 = time.perf_counter()
        path, expanded = fn(grid, s, t)
        dt = (time.perf_counter() - t0) * 1000
        paths[name] = path
        print(f"{name:<20}{len(path) - 1:>7}{bends(path):>7}{expanded:>10}{dt:>10.3f}")
    print(f"(Manhattan lower bound = {md(s, t)})")
    for name in show:
        print(f"\n{name}:")
        print(draw(grid, {"X": (s, t)}, {"X": paths[name]}))
    print()


def part_a():
    compare_single_net("chip 1 (open)", OPEN_CHIP, (9, 0), (0, 19), ["Lee (BFS)"])
    compare_single_net("chip 2 (blocked)", BLOCKED_CHIP, (6, 0), (6, 19),
                       [name for name, _ in SINGLE_NET_METHODS])


def part_b():
    print("--- Part B: several nets on one layer ---")
    grid = Grid(7, 12)
    nets = MULTI_NET_NETS
    for label, routes in [
        ("given order A,B,C", route_sequential(grid, nets, ["A", "B", "C"])),
        ("shortest net first", route_sequential(grid, nets, sorted(nets, key=lambda n: md(*nets[n])))),
        ("rip-up & reroute (order A,B,C)", route_ripup(grid, nets, ["A", "B", "C"])[0]),
    ]:
        check_routes(grid, nets, routes)
        print(f"\n{label}: routed {len(routes)}/{len(nets)} nets, "
              f"total wire length {total_length(routes)}")
        print(draw(grid, nets, routes))

    # Random benchmark
    n_inst = 200
    stats = {"given order": [0, 0], "shortest first": [0, 0], "rip-up & reroute": [0, 0]}
    for seed in range(n_inst):
        grid, nets = random_instance(seed)
        order = list(nets)
        results = {
            "given order": route_sequential(grid, nets, order),
            "shortest first": route_sequential(grid, nets, sorted(nets, key=lambda n: md(*nets[n]))),
            "rip-up & reroute": route_ripup(grid, nets, order)[0],
        }
        for k, routes in results.items():
            check_routes(grid, nets, routes)
            stats[k][0] += len(routes)
            stats[k][1] += len(routes) == len(nets)
    print(f"\nRandom benchmark: {n_inst} chips, 12x12 grid, 6 nets, 4 random macros each")
    print(f"{'strategy':<20}{'nets routed':>14}{'chips fully routed':>20}")
    for k, (routed, full) in stats.items():
        print(f"{k:<20}{routed:>8}/{6 * n_inst:<5}{full:>14}/{n_inst}")


def main():
    print("=== IC wire routing ===")
    part_a()
    part_b()


if __name__ == "__main__":
    main()
