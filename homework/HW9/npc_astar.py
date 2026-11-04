"""Problem 4 - NPC searching for the player, solved with A*.

Game map: '#' wall, '.' road (cost 1), '~' swamp (cost 5, slow to cross),
'N' = NPC, 'P' = player.  Moving is 4-directional.

A* expands the node with the smallest
        f(n) = g(n) + h(n)
    g(n) = real cost from the NPC to n
    h(n) = estimated cost from n to the player = Manhattan distance
Because every step costs at least 1, Manhattan distance never overestimates the
real cost (it is admissible and consistent), so A* returns an optimal path.

The script compares A* with
    * Dijkstra            (h = 0: optimal but expands more nodes)
    * Greedy best-first   (only h: fast but not optimal)
    * BFS                 (ignores terrain cost: fewest steps, not cheapest)
and then runs a small chase where the player wanders and the NPC re-plans with
A* every turn.
"""
import heapq
import random
from collections import deque

MAP_TEXT = """\
####################
#N.....#...........#
#.####.#.#######.#.#
#.#....#.#.....#.#.#
#.#.####.#.###.#.#.#
#.#......#..~#.#...#
#.######.###~#.###.#
#......#.~~~~#.....#
######.#.~~~~#####.#
#......#.~~~~.....P#
#.######.#######.###
#..................#
####################"""

COST = {".": 1, "~": 5, "N": 1, "P": 1}
DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def parse(text):
    grid = [list(row) for row in text.splitlines()]
    npc = player = None
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == "N":
                npc = (r, c)
            elif ch == "P":
                player = (r, c)
    return grid, npc, player


def neighbours(grid, cell):
    r, c = cell
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != "#":
            yield (nr, nc)


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def best_first(grid, start, goal, mode="astar", trace=None):
    """Generic best-first search.
    mode: 'astar'    priority = g + h
          'dijkstra' priority = g
          'greedy'   priority = h
    Returns (path, cost, nodes_expanded).  If trace is a set, the expanded cells are
    added to it (used by visualize.py)."""
    g = {start: 0}
    parent = {start: None}
    counter = 0                                  # tie-breaker for the heap
    open_heap = [(0, 0, counter, start)]
    closed = set()
    while open_heap:
        _, _, _, cell = heapq.heappop(open_heap)
        if cell in closed:
            continue
        closed.add(cell)
        if cell == goal:
            break
        for nxt in neighbours(grid, cell):
            new_g = g[cell] + COST[grid[nxt[0]][nxt[1]]]
            if mode == "greedy":
                if nxt in parent:                # greedy: first discovery wins
                    continue
            elif nxt in g and new_g >= g[nxt]:
                continue
            g[nxt] = new_g
            parent[nxt] = cell
            h = manhattan(nxt, goal)
            pri = {"astar": new_g + h, "dijkstra": new_g, "greedy": h}[mode]
            counter += 1
            heapq.heappush(open_heap, (pri, h, counter, nxt))
    if trace is not None:
        trace.update(closed)
    if goal not in parent:
        return None, float("inf"), len(closed)
    path = reconstruct(parent, goal)
    return path, path_cost(grid, path), len(closed)


def bfs(grid, start, goal, trace=None):
    """Unweighted BFS: fewest moves, ignores terrain cost."""
    parent = {start: None}
    q = deque([start])
    expanded = 0
    while q:
        cell = q.popleft()
        expanded += 1
        if trace is not None:
            trace.add(cell)
        if cell == goal:
            break
        for nxt in neighbours(grid, cell):
            if nxt not in parent:
                parent[nxt] = cell
                q.append(nxt)
    path = reconstruct(parent, goal)
    return path, path_cost(grid, path), expanded


def reconstruct(parent, goal):
    path, cell = [], goal
    while cell is not None:
        path.append(cell)
        cell = parent[cell]
    return path[::-1]


def path_cost(grid, path):
    return sum(COST[grid[r][c]] for r, c in path[1:])


def draw(grid, path, npc=None, player=None):
    g = [[("." if ch in "NP" else ch) for ch in row] for row in grid]
    for r, c in path[1:-1]:
        g[r][c] = "*"
    if npc:
        g[npc[0]][npc[1]] = "N"
    if player:
        g[player[0]][player[1]] = "P"
    return "\n".join("".join(row) for row in g)


def chase(grid, npc, player, seed=0, max_turns=200, log=None):
    """The player wanders randomly (it does not know where the NPC is); the NPC moves
    one cell per turn along a freshly computed A* path, because the target keeps moving.
    Returns (turns, total_nodes_expanded); turns is None if not caught in max_turns.
    If log is a list, (npc, player) positions are appended after every move."""
    rng = random.Random(seed)
    total_expanded = 0
    if log is not None:
        log.append((npc, player))
    for turn in range(1, max_turns + 1):
        path, _, expanded = best_first(grid, npc, player, "astar")
        total_expanded += expanded
        npc = path[1] if len(path) > 1 else npc        # NPC step
        if log is not None:
            log.append((npc, player))
        if npc == player:
            return turn, total_expanded
        player = rng.choice(list(neighbours(grid, player)))   # player step
        if log is not None:
            log.append((npc, player))
        if npc == player:
            return turn, total_expanded
    return None, total_expanded


def main():
    grid, npc, player = parse(MAP_TEXT)
    print("=== NPC searching for the player (A*) ===")
    print(f"NPC at {npc}, player at {player}, road cost 1, swamp '~' cost 5\n")
    results = {}
    print(f"{'method':<20}{'cost':>6}{'steps':>7}{'expanded':>10}")
    for name, fn in [("A* (Manhattan)", lambda: best_first(grid, npc, player, "astar")),
                     ("Dijkstra (h=0)", lambda: best_first(grid, npc, player, "dijkstra")),
                     ("Greedy best-first", lambda: best_first(grid, npc, player, "greedy")),
                     ("BFS (ignores cost)", lambda: bfs(grid, npc, player))]:
        path, cost, expanded = fn()
        results[name] = path
        print(f"{name:<20}{cost:>6}{len(path) - 1:>7}{expanded:>10}")

    print("\nA* path ('*'):")
    print(draw(grid, results["A* (Manhattan)"], npc, player))
    print("\nBFS path (shortest in steps, goes through the swamp):")
    print(draw(grid, results["BFS (ignores cost)"], npc, player))
    print("\nGreedy best-first path:")
    print(draw(grid, results["Greedy best-first"], npc, player))

    print("\nChase simulation (player wanders randomly, NPC re-plans with A* each turn):")
    for seed in range(5):
        turns, exp = chase(grid, npc, player, seed)
        status = f"caught after {turns} turns" if turns else "not caught in 200 turns"
        print(f"  seed {seed}: {status}, {exp} nodes expanded in total")


if __name__ == "__main__":
    main()
