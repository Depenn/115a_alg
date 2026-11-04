"""Checks for all five problems.  Run:  python test_search.py   (or: pytest test_search.py)"""
import random

import ic_routing as ic
import maze_dfs
import npc_astar
import queens_dfs
import river_bfs


def valid_grid_path(path, passable):
    return all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(path, path[1:])) \
        and all(passable(c) for c in path)


def test_maze():
    grid, s, e = maze_dfs.parse(maze_dfs.MAZE_TEXT)
    open_cell = lambda c: grid[c[0]][c[1]] != "#"
    p1, _ = maze_dfs.dfs_recursive(grid, s, e)
    p2, _ = maze_dfs.dfs_iterative(grid, s, e)
    best = maze_dfs.bfs_shortest(grid, s, e)
    for p in (p1, p2, best):
        assert p[0] == s and p[-1] == e and valid_grid_path(p, open_cell)
        assert len(set(p)) == len(p)                 # simple path, no repeated cell
    assert len(best) <= len(p1)
    # unreachable exit -> None
    blocked = [row[:] for row in grid]
    er, ec = e
    blocked[er][ec + 1] = "#"                        # the only open cell next to E
    assert maze_dfs.dfs_recursive(blocked, s, e)[0] is None
    assert maze_dfs.dfs_iterative(blocked, s, e)[0] is None


def test_river():
    path, _ = river_bfs.bfs()
    assert path[0][1] == river_bfs.START and path[-1][1] == river_bfs.GOAL
    assert len(path) - 1 == 7
    for (_, a), (_, b) in zip(path, path[1:]):
        assert river_bfs.is_safe(b)
        assert b in [nxt for _, nxt in river_bfs.moves(a)]
    assert len(river_bfs.all_shortest()) == 2


def test_queens():
    sols, _ = queens_dfs.solve_queens(8)
    assert len(sols) == 92 and len(set(sols)) == 92
    assert all(queens_dfs.is_valid(s) for s in sols)
    assert len({queens_dfs.canonical(s) for s in sols}) == 12
    known = {4: 2, 5: 10, 6: 4, 7: 40, 9: 352, 10: 724}
    for n, count in known.items():
        assert len(queens_dfs.solve_queens(n)[0]) == count
    assert queens_dfs.brute_force_count(6) == 4      # cross-check with brute force


def test_npc():
    grid, npc, player = npc_astar.parse(npc_astar.MAP_TEXT)
    passable = lambda c: grid[c[0]][c[1]] != "#"
    a = npc_astar.best_first(grid, npc, player, "astar")
    d = npc_astar.best_first(grid, npc, player, "dijkstra")
    g = npc_astar.best_first(grid, npc, player, "greedy")
    b = npc_astar.bfs(grid, npc, player)
    for path, _, _ in (a, d, g, b):
        assert path[0] == npc and path[-1] == player and valid_grid_path(path, passable)
    assert a[1] == d[1]                    # A* is optimal (same cost as Dijkstra)
    assert a[2] <= d[2]                    # ...and expands no more nodes
    assert g[1] >= a[1] and b[1] >= a[1]
    assert len(b[0]) <= len(a[0])          # BFS has the fewest steps
    # A* = Dijkstra on random weighted maps
    for seed in range(30):
        rng = random.Random(seed)
        rows = ["".join(rng.choice("..~#") for _ in range(15)) for _ in range(10)]
        rows[0] = "N" + rows[0][1:]
        rows[-1] = rows[-1][:-1] + "P"
        gr, s, t = npc_astar.parse("\n".join(rows))
        ra = npc_astar.best_first(gr, s, t, "astar")
        rd = npc_astar.best_first(gr, s, t, "dijkstra")
        assert ra[1] == rd[1]


def test_routing_single_net():
    for seed in range(100):
        grid, nets = ic.random_instance(seed, n_nets=1, n_blocks=8)
        s, t = nets["A"]
        lee, _ = ic.lee(grid, s, t)
        if lee is None:
            for _, fn in ic.SINGLE_NET_METHODS:
                assert fn(grid, s, t)[0] is None
            continue
        free = lambda c: c not in grid.blocked
        paths = {}
        for name, fn in ic.SINGLE_NET_METHODS:
            p, _ = fn(grid, s, t)
            paths[name] = p
            assert p[0] == s and p[-1] == t and valid_grid_path(p, free), name
            if name in ("Lee (BFS)", "Hadlock (0-1 BFS)", "A* (Manhattan)"):
                assert len(p) == len(lee), name     # these three are always shortest
            else:
                assert len(p) >= len(lee), name
        # bend-penalty A* minimises length + 5*bends, so nothing else may beat it on that,
        # and it never has more bends than a shortest path
        cost = lambda p: (len(p) - 1) + 5 * ic.bends(p)
        bp = paths["A* + bend penalty"]
        assert all(cost(bp) <= cost(p) for p in paths.values())
        shortest = [p for p in paths.values() if len(p) == len(lee)]
        assert ic.bends(bp) <= min(ic.bends(p) for p in shortest)


def test_routing_multi_net():
    grid = ic.Grid(7, 12)
    nets = ic.MULTI_NET_NETS
    assert len(ic.route_sequential(grid, nets, ["A", "B", "C"])) == 1
    assert len(ic.route_sequential(grid, nets, ["B", "C", "A"])) == 3
    routes, _ = ic.route_ripup(grid, nets, ["A", "B", "C"])
    assert len(routes) == 3 and ic.check_routes(grid, nets, routes)
    for seed in range(50):
        grid, nets = ic.random_instance(seed)
        for routes in (ic.route_sequential(grid, nets, list(nets)),
                       ic.route_ripup(grid, nets, list(nets))[0]):
            assert ic.check_routes(grid, nets, routes)   # no shorts, wires connected


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"all {len(tests)} tests passed")
