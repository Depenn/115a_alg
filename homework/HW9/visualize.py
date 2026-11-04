"""Draws every figure used in README.md into images/.   Run:  python visualize.py

All numbers in the figures come from running the solvers in this folder; nothing is
typed in by hand.  Needs matplotlib and numpy.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Patch, Rectangle  # noqa: E402

import ic_routing as ic  # noqa: E402
import maze_dfs  # noqa: E402
import npc_astar  # noqa: E402
import queens_dfs  # noqa: E402
import river_bfs  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")

# ---- palette (reference data-viz palette, light mode; categorical order validated) ----
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
HAIR = "#e1e0d9"
BASE = "#c3c2b7"
FLOOR = "#f0efec"
WALL = "#3d3c39"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"       # blue, orange, aqua
BLUE_100, BLUE_150, BLUE_250 = "#cde2fb", "#b7d3f6", "#86b6ef"
ORANGE_TINT = "#f8cfbd"
SWAMP = "#d9d2b4"
MACRO = "#a9a79d"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"],
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titleweight": "semibold",
    "axes.titlecolor": INK,
    "axes.labelcolor": INK2,
    "axes.edgecolor": BASE,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "legend.frameon": False,
})


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("wrote", os.path.relpath(path))


# ------------------------------------------------------------------ grid helpers
def tile_grid(ax, colors):
    """Draw a grid of coloured tiles separated by a thin surface-coloured gap."""
    rows, cols = len(colors), len(colors[0])
    img = np.array([[to_rgb(c) for c in row] for row in colors])
    ax.imshow(img, interpolation="nearest")
    ax.set_xticks(np.arange(-0.5, cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, rows, 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=1.2)
    ax.tick_params(which="both", length=0, labelbottom=False, labelleft=False)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)


def draw_path(ax, path, color=S1, lw=3.0, z=4, offset=(0, 0)):
    ys = [r + offset[0] for r, _ in path]
    xs = [c + offset[1] for _, c in path]
    ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="round",
            solid_joinstyle="round", zorder=z)


def badge(ax, cell, text, face=INK, fg="white", r=0.42, z=6):
    rr, cc = cell
    ax.add_patch(Circle((cc, rr), r, facecolor=face, edgecolor=SURFACE, lw=1.5, zorder=z))
    ax.text(cc, rr, text, ha="center", va="center", color=fg, fontsize=8.5,
            fontweight="bold", zorder=z + 1)


def corner_marks(ax, path, color=INK):
    """Small squares on every bend of a wire (a via in a two-layer router)."""
    for a, b, c in zip(path, path[1:], path[2:]):
        if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
            ax.add_patch(Rectangle((b[1] - 0.17, b[0] - 0.17), 0.34, 0.34,
                                   facecolor=SURFACE, edgecolor=color, lw=1.4, zorder=5))


# ============================================================== 1. maze (DFS)
def fig_maze():
    grid, s, e = maze_dfs.parse(maze_dfs.MAZE_TEXT)
    dfs_path, visited = maze_dfs.dfs_recursive(grid, s, e)
    bfs_path = maze_dfs.bfs_shortest(grid, s, e)
    on_path = set(dfs_path)

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.6))
    fig.subplots_adjust(left=0.03, right=0.97, wspace=0.12)
    for ax, path, title, dead in [
        (axes[0], dfs_path, f"DFS: {len(dfs_path) - 1} steps, {len(visited)} cells visited", True),
        (axes[1], bfs_path, f"BFS (for comparison): {len(bfs_path) - 1} steps, the shortest", False),
    ]:
        colors = [[WALL if ch == "#" else FLOOR for ch in row] for row in grid]
        if dead:
            for r, c in visited - on_path:
                colors[r][c] = ORANGE_TINT
        tile_grid(ax, colors)
        draw_path(ax, path, S1)
        badge(ax, s, "S", S1)
        badge(ax, e, "E", INK)
        ax.set_title(title, loc="left")
    handles = [Line2D([], [], color=S1, lw=3, label="path found"),
               Patch(facecolor=ORANGE_TINT, label="dead end: DFS went in, then backtracked"),
               Patch(facecolor=WALL, label="wall")]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("Rat in a maze: DFS tries 'right' first, runs into the dead end on the right, "
                 "backs out", x=0.02, ha="left", fontsize=12, fontweight="bold", color=INK)
    save(fig, "maze_dfs.png")


# ===================================================== 2. river crossing (BFS)
ITEM_COLOR = {"farmer": INK2, "wolf": S1, "goat": S2, "cabbage": S3}
LETTER = {"farmer": "F", "wolf": "W", "goat": "G", "cabbage": "C"}


def fig_river_story():
    path, _ = river_bfs.bfs()
    n = len(path)
    fig, ax = plt.subplots(figsize=(8.6, 0.78 * n + 0.6))
    L0, L1, R0, R1 = 0.0, 3.6, 6.4, 10.0
    left_x = [0.55, 1.4, 2.25, 3.1]
    right_x = [6.9, 7.75, 8.6, 9.45]
    for i, (who, state) in enumerate(path):
        y = -i
        ax.add_patch(FancyBboxPatch((L0, y - 0.36), L1 - L0, 0.72, boxstyle="round,pad=0,rounding_size=0.12",
                                    facecolor=FLOOR, edgecolor="none"))
        ax.add_patch(FancyBboxPatch((R0, y - 0.36), R1 - R0, 0.72, boxstyle="round,pad=0,rounding_size=0.12",
                                    facecolor=FLOOR, edgecolor="none"))
        ax.add_patch(Rectangle((L1 + 0.15, y - 0.36), R0 - L1 - 0.3, 0.72, facecolor=BLUE_100, edgecolor="none"))
        for k, name in enumerate(river_bfs.NAMES):
            x = left_x[k] if state[k] == 0 else right_x[k]
            ax.add_patch(Circle((x, y), 0.3, facecolor=ITEM_COLOR[name], edgecolor=SURFACE, lw=1.5))
            ax.text(x, y, LETTER[name], ha="center", va="center", color="white",
                    fontsize=10, fontweight="bold")
        if i == 0:
            ax.text(-0.25, y, "start", ha="right", va="center", color=INK2, fontsize=10)
            continue
        going = state[0] == 1
        arrow = "→" if going else "←"
        cargo = who or "alone"
        ax.text(-0.25, y, f"{i}.", ha="right", va="center", color=INK2, fontsize=10, fontweight="bold")
        ax.text(5.0, y, f"{arrow}  {cargo}  {arrow}" if cargo != "alone" else f"{arrow}  farmer alone  {arrow}",
                ha="center", va="center", color=INK, fontsize=9.5)
        if who == "goat" and not going:
            ax.text(R1 + 0.25, y, "the goat goes BACK:\nthe step a greedy\nsearch never tries",
                    ha="left", va="center", color=S2, fontsize=8.5, fontweight="semibold")
    ax.text((L0 + L1) / 2, 0.65, "start bank", ha="center", color=INK2, fontsize=10)
    ax.text((R0 + R1) / 2, 0.65, "goal bank", ha="center", color=INK2, fontsize=10)
    ax.text(5.0, 0.65, "river", ha="center", color=S1, fontsize=10)
    ax.set_xlim(-1.0, 12.4)
    ax.set_ylim(-n + 0.4, 1.05)
    ax.set_aspect("equal")
    ax.axis("off")
    handles = [Line2D([], [], marker="o", ls="", markersize=11, markerfacecolor=ITEM_COLOR[k],
                      markeredgecolor=SURFACE, label=f"{LETTER[k]} = {k}") for k in river_bfs.NAMES]
    ax.legend(handles=handles, loc="upper center", ncol=4, bbox_to_anchor=(0.43, 0.0))
    ax.set_title(f"Wolf, goat, cabbage: the BFS plan uses the minimum of {n - 1} crossings",
                 loc="left", fontsize=12)
    save(fig, "river_steps.png")


def state_label(state):
    left = "".join(LETTER[n] for n, s in zip(river_bfs.NAMES, state) if s == 0) or "–"
    right = "".join(LETTER[n] for n, s in zip(river_bfs.NAMES, state) if s == 1) or "–"
    return f"{left} | {right}"


def fig_river_graph():
    from collections import deque
    depth = {river_bfs.START: 0}
    q = deque([river_bfs.START])
    edges = set()
    while q:
        s = q.popleft()
        for _, nxt in river_bfs.moves(s):
            edges.add(frozenset((s, nxt)))
            if nxt not in depth:
                depth[nxt] = depth[s] + 1
                q.append(nxt)
    sols = river_bfs.all_shortest()
    sol_edges = [{frozenset((a[1], b[1])) for a, b in zip(sol, sol[1:])} for sol in sols]
    both = sol_edges[0] & sol_edges[1]

    layers = {}
    for st, d in depth.items():
        layers.setdefault(d, []).append(st)
    pos = {}
    for d, sts in layers.items():
        sts.sort(key=lambda st: (st[1], st[3]))           # wolf-across states on top
        for k, st in enumerate(sts):
            pos[st] = (d * 1.6, (len(sts) - 1) / 2 - k)

    fig, ax = plt.subplots(figsize=(10, 3.3))
    for e in edges:
        a, b = tuple(e)
        (x1, y1), (x2, y2) = pos[a], pos[b]
        if e in both:
            ax.plot([x1, x2], [y1, y2], color=INK, lw=2.4, zorder=1)
        elif e in sol_edges[0]:
            ax.plot([x1, x2], [y1, y2], color=S1, lw=2.4, zorder=1)
        elif e in sol_edges[1]:
            ax.plot([x1, x2], [y1, y2], color=S2, lw=2.4, zorder=1)
        else:
            ax.plot([x1, x2], [y1, y2], color=BASE, lw=1.2, zorder=0)
    for st, (x, y) in pos.items():
        goal = st == river_bfs.GOAL
        start = st == river_bfs.START
        ax.add_patch(FancyBboxPatch((x - 0.62, y - 0.2), 1.24, 0.4,
                                    boxstyle="round,pad=0,rounding_size=0.12",
                                    facecolor=INK if (goal or start) else SURFACE,
                                    edgecolor=INK, lw=1.2, zorder=2))
        ax.text(x, y, state_label(st), ha="center", va="center", fontsize=9,
                color="white" if (goal or start) else INK, zorder=3, fontweight="semibold")
    for d in layers:
        ax.text(d * 1.6, -1.05, f"{d}", ha="center", color=MUTED, fontsize=9)
    ax.text(-0.75, -1.05, "crossings:", ha="right", color=MUTED, fontsize=9)
    ax.set_xlim(-1.9, 7 * 1.6 + 0.8)
    ax.set_ylim(-1.25, 0.95)
    ax.axis("off")
    handles = [Line2D([], [], color=INK, lw=2.4, label="used by both shortest plans"),
               Line2D([], [], color=S1, lw=2.4, label="plan 1: wolf first"),
               Line2D([], [], color=S2, lw=2.4, label="plan 2: cabbage first")]
    ax.legend(handles=handles, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.13))
    ax.set_title(f"All {len(depth)} safe states, laid out by BFS level "
                 "(left bank | right bank)", loc="left", fontsize=12, pad=24)
    save(fig, "river_graph.png")


# ======================================================= 3. eight queens (DFS)
def draw_board(ax, sol, queen_size=20):
    n = len(sol)
    for r in range(n):
        for c in range(n):
            ax.add_patch(Rectangle((c, r), 1, 1, facecolor=FLOOR if (r + c) % 2 == 0 else BASE,
                                   edgecolor="none"))
    for r, c in enumerate(sol):
        ax.text(c + 0.5, r + 0.55, "♛", ha="center", va="center", fontsize=queen_size,
                color=INK, fontfamily="DejaVu Sans")
    ax.set_xlim(0, n)
    ax.set_ylim(n, 0)
    ax.set_aspect("equal")
    ax.axis("off")


def fig_queens():
    sols, nodes = queens_dfs.solve_queens(8)
    first, first_nodes = queens_dfs.solve_queens(8, first_only=True)
    unique = sorted({queens_dfs.canonical(s) for s in sols})

    fig, ax = plt.subplots(figsize=(4.6, 4.9))
    draw_board(ax, first[0], 22)
    for r in range(8):
        ax.text(-0.15, r + 0.5, f"row {r}", ha="right", va="center", color=MUTED, fontsize=8.5)
        ax.text(r + 0.5, 8.1, str(r), ha="center", va="top", color=MUTED, fontsize=8.5)
    ax.text(4, 8.65, "column", ha="center", va="top", color=MUTED, fontsize=8.5)
    ax.set_title(f"First solution found: {first[0]}\n"
                 f"after {first_nodes} column tries ({len(sols)} solutions in total, "
                 f"{len(unique)} distinct)", loc="left", fontsize=10.5)
    save(fig, "queens_board.png")


def fig_queens_unique():
    sols, _ = queens_dfs.solve_queens(8)
    unique = sorted({queens_dfs.canonical(s) for s in sols})
    fig, axes = plt.subplots(2, 6, figsize=(11, 4.2))
    for ax, sol in zip(axes.flat, unique):
        draw_board(ax, sol, 9)
        ax.set_title("".join(map(str, sol)), fontsize=8.5, color=INK2, fontweight="normal")
    fig.suptitle(f"The {len(unique)} essentially different solutions (each stands for up to 8 of the "
                 f"{len(sols)} by rotation/reflection)", x=0.02, ha="left", fontsize=12, fontweight="bold")
    save(fig, "queens_unique.png")


def fig_queens_pruning():
    ns = list(range(4, 11))
    tries = [queens_dfs.solve_queens(n)[1] for n in ns]
    brute = [n ** n for n in ns]
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    ax.plot(ns, brute, color=S2, lw=2, marker="o", markersize=7, markeredgecolor=SURFACE,
            markeredgewidth=2, label="brute force: nⁿ placements")
    ax.plot(ns, tries, color=S1, lw=2, marker="o", markersize=7, markeredgecolor=SURFACE,
            markeredgewidth=2, label="DFS + backtracking: column tries")
    ax.set_yscale("log")
    ax.grid(axis="y", color=HAIR, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0)
    ax.set_xticks(ns)
    ax.set_xlabel("board size n")
    ax.set_ylabel("work (log scale)")
    i8 = ns.index(8)
    ax.annotate(f"{brute[i8]:,}", (8, brute[i8]), textcoords="offset points", xytext=(-8, 8),
                ha="right", color=INK2, fontsize=9)
    ax.annotate(f"{tries[i8]:,}", (8, tries[i8]), textcoords="offset points", xytext=(6, -14),
                ha="left", color=INK2, fontsize=9)
    ax.text(10.15, brute[-1], "brute force", va="center", color=INK2, fontsize=9)
    ax.text(10.15, tries[-1], "backtracking", va="center", color=INK2, fontsize=9)
    ax.set_xlim(3.7, 11.2)
    ax.legend(loc="upper left")
    ax.set_title(f"Pruning: at n = 8 backtracking does about {brute[i8] // tries[i8]:,}× less work",
                 loc="left")
    save(fig, "queens_pruning.png")


# =================================================================== 4. NPC (A*)
def npc_colors(grid):
    return [[WALL if ch == "#" else SWAMP if ch == "~" else FLOOR for ch in row] for row in grid]


def fig_npc():
    grid, npc, player = npc_astar.parse(npc_astar.MAP_TEXT)
    runs = []
    for name, fn in [("A* (g + Manhattan h)", lambda tr: npc_astar.best_first(grid, npc, player, "astar", tr)),
                     ("Dijkstra (g only)", lambda tr: npc_astar.best_first(grid, npc, player, "dijkstra", tr)),
                     ("Greedy best-first (h only)", lambda tr: npc_astar.best_first(grid, npc, player, "greedy", tr)),
                     ("BFS (ignores terrain cost)", lambda tr: npc_astar.bfs(grid, npc, player, tr))]:
        tr = set()
        path, cost, expanded = fn(tr)
        runs.append((name, path, cost, expanded, tr))

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.0))
    for ax, (name, path, cost, expanded, tr) in zip(axes.flat, runs):
        colors = npc_colors(grid)
        for r, c in tr:
            if grid[r][c] != "~":
                colors[r][c] = BLUE_150
            else:
                colors[r][c] = "#a9b8c8"
        tile_grid(ax, colors)
        draw_path(ax, path, S2, lw=3)
        badge(ax, npc, "N", S1)
        badge(ax, player, "P", INK)
        ax.set_title(f"{name}\ncost {cost} · {len(path) - 1} steps · {expanded} cells expanded",
                     loc="left", fontsize=10.5)
    handles = [Line2D([], [], color=S2, lw=3, label="path"),
               Patch(facecolor=BLUE_150, label="expanded cell"),
               Patch(facecolor=SWAMP, label="swamp (cost 5)"),
               Patch(facecolor="#a9b8c8", label="expanded swamp"),
               Patch(facecolor=FLOOR, label="road (cost 1)"),
               Patch(facecolor=WALL, label="wall")]
    fig.legend(handles=handles, loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.02), fontsize=9)
    fig.suptitle("NPC → player: A* finds the cheapest path while expanding fewer cells than Dijkstra",
                 x=0.02, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0.03, 1, 0.97), h_pad=2.5)
    save(fig, "npc_search.png")

    # small multiples: one measure per panel, never two y-scales
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 2.9))
    names = [r[0].split(" (")[0] for r in runs]
    for ax, idx, title in [(axes[0], 2, "Path cost (lower is better)"),
                           (axes[1], 3, "Cells expanded (lower is faster)")]:
        vals = [r[idx] for r in runs]
        y = np.arange(len(vals))[::-1]
        ax.barh(y, vals, color=S1, height=0.6)
        for yy, v in zip(y, vals):
            ax.text(v + max(vals) * 0.02, yy, str(v), va="center", color=INK2, fontsize=9)
        ax.set_yticks(y, names)
        ax.tick_params(length=0, labelcolor=INK)
        ax.set_xticks([])
        for sp in ("top", "right", "bottom"):
            ax.spines[sp].set_visible(False)
        ax.set_xlim(0, max(vals) * 1.15)
        ax.set_title(title, loc="left", fontsize=10.5)
    fig.tight_layout()
    save(fig, "npc_compare.png")


def fig_npc_chase(seed=2):
    grid, npc, player = npc_astar.parse(npc_astar.MAP_TEXT)
    log = []
    turns, _ = npc_astar.chase(grid, npc, player, seed, log=log)
    npc_track = [log[0][0]] + [log[i][0] for i in range(1, len(log), 2)]
    player_track = [p for _, p in log[::2]] + [log[-1][1]]
    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    tile_grid(ax, npc_colors(grid))
    draw_path(ax, player_track, S2, lw=2.2, offset=(0.12, 0.12))
    draw_path(ax, npc_track, S1, lw=2.6, offset=(-0.12, -0.12))
    badge(ax, npc, "N", S1, r=0.38)
    badge(ax, player, "P", S2, r=0.38)
    cr, cc = log[-1][0]
    ax.plot(cc, cr, marker="*", markersize=20, color=INK, markeredgecolor=SURFACE, zorder=8)
    handles = [Line2D([], [], color=S1, lw=2.6, label="NPC (re-plans with A* every turn)"),
               Line2D([], [], color=S2, lw=2.2, label="player (random walk)"),
               Line2D([], [], marker="*", ls="", markersize=14, color=INK, label=f"caught (turn {turns})")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=3, fontsize=9)
    ax.set_title(f"Chase, seed {seed}: the target moves, so the NPC re-runs A* every turn",
                 loc="left")
    save(fig, "npc_chase.png")


# ============================================================ 5. IC wire routing
def chip_colors(grid, explored=()):
    colors = [[MACRO if (r, c) in grid.blocked else FLOOR for c in range(grid.cols)]
              for r in range(grid.rows)]
    for r, c in explored:
        colors[r][c] = BLUE_150
    return colors


def pin(ax, cell, text, face=INK):
    r, c = cell
    ax.add_patch(Rectangle((c - 0.42, r - 0.42), 0.84, 0.84, facecolor=face, edgecolor=SURFACE,
                           lw=1.2, zorder=7))
    ax.text(c, r, text, ha="center", va="center", color="white", fontsize=8,
            fontweight="bold", zorder=8)


def fig_ic_single():
    configs = [("chip 1: open", ic.OPEN_CHIP, (9, 0), (0, 19)),
               ("chip 2: blocked", ic.BLOCKED_CHIP, (6, 0), (6, 19))]
    for label, chip, s, t in configs:
        grid = ic.Grid.from_text(chip)
        fig, axes = plt.subplots(2, 3, figsize=(12.5, 6.4))
        for ax, (name, fn) in zip(axes.flat, ic.SINGLE_NET_METHODS):
            tr = set()
            path, expanded = fn(grid, s, t, trace=tr)
            tile_grid(ax, chip_colors(grid, tr))
            draw_path(ax, path, S1, lw=2.8)
            corner_marks(ax, path)
            pin(ax, s, "S")
            pin(ax, t, "T")
            unit = "states" if "bend" in name else "cells"
            nb = ic.bends(path)
            ax.set_title(f"{name}\nlength {len(path) - 1} · {nb} bend{'' if nb == 1 else 's'} · "
                         f"{expanded} {unit} expanded", loc="left", fontsize=10)
        legend_ax = axes.flat[-1]
        legend_ax.axis("off")
        handles = [Line2D([], [], color=S1, lw=2.8, label="wire"),
                   Line2D([], [], marker="s", ls="", markersize=8, markerfacecolor=SURFACE,
                          markeredgecolor=INK, label="bend (= a via on 2 layers)"),
                   Patch(facecolor=BLUE_150, label="cell expanded by the search"),
                   Patch(facecolor=MACRO, label="macro (blocked)"),
                   Patch(facecolor=INK, label="pin S / T")]
        legend_ax.legend(handles=handles, loc="center left", fontsize=10, labelspacing=1.0)
        legend_ax.text(0.0, 0.05, f"Manhattan lower bound = {ic.md(s, t)}", transform=legend_ax.transAxes,
                       color=INK2, fontsize=10)
        fig.suptitle(f"IC routing, one net, {label}", x=0.02, ha="left",
                     fontsize=12, fontweight="bold")
        fig.tight_layout(rect=(0, 0, 1, 0.96), h_pad=2.5)
        save(fig, f"ic_single_{'open' if 'open' in label else 'blocked'}.png")


NET_COLOR = {"A": S1, "B": S2, "C": S3}


def draw_nets(ax, grid, nets, routes, title, ripped=()):
    tile_grid(ax, chip_colors(grid))
    for name, (s, t) in nets.items():
        if name in routes:
            draw_path(ax, routes[name], NET_COLOR[name], lw=3.2)
        else:   # unrouted: thin dashed "flyline" straight between the pins, as EDA tools show it
            ax.plot([s[1], t[1]], [s[0], t[0]], color=NET_COLOR[name], lw=1.4, ls=(0, (3, 2)), zorder=3)
    for name, (s, t) in nets.items():
        face = NET_COLOR[name]
        pin(ax, s, name, face)
        pin(ax, t, name, face)
    ax.set_title(title, loc="left", fontsize=10)


def fig_ic_multi():
    grid = ic.Grid(7, 12)
    nets = ic.MULTI_NET_NETS
    shortest_order = sorted(nets, key=lambda n: ic.md(*nets[n]))
    cases = [("given order A, B, C", ic.route_sequential(grid, nets, ["A", "B", "C"])),
             ("shortest net first (" + ", ".join(shortest_order) + ")",
              ic.route_sequential(grid, nets, shortest_order)),
             ("rip-up & reroute, starting from A, B, C", ic.route_ripup(grid, nets, ["A", "B", "C"])[0])]
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.3))
    for ax, (label, routes) in zip(axes, cases):
        draw_nets(ax, grid, nets, routes,
                  f"{label}\n{len(routes)}/{len(nets)} nets routed · wire length {ic.total_length(routes)}")
    handles = [Line2D([], [], color=INK2, lw=3.2, label="routed wire"),
               Line2D([], [], color=INK2, lw=1.4, ls=(0, (3, 2)), label="unrouted net (flyline)")] + \
              [Patch(facecolor=NET_COLOR[n], label=f"net {n}") for n in nets]
    fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.08))
    fig.suptitle("Many nets, one layer: wires cannot cross, so the routing order matters",
                 x=0.02, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    save(fig, "ic_multi.png")

    log = []
    ic.route_ripup(grid, nets, ["A", "B", "C"], log=log)
    fig, axes = plt.subplots(1, len(log), figsize=(3.4 * len(log), 2.9))
    for k, (ax, (name, ripped, routes)) in enumerate(zip(axes, log), 1):
        what = f"route {name}" + (f", rip up {', '.join(ripped)}" if ripped else "")
        draw_nets(ax, grid, nets, routes, f"step {k}: {what}")
    fig.suptitle("Rip-up & reroute, step by step (B cannot be routed legally, so it goes through A "
                 "and A is ripped up)", x=0.02, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    save(fig, "ic_ripup_steps.png")


def fig_ic_benchmark(n_inst=200):
    stats = {"given order": [0, 0], "shortest first": [0, 0], "rip-up & reroute": [0, 0]}
    n_nets = 6
    for seed in range(n_inst):
        grid, nets = ic.random_instance(seed)
        order = list(nets)
        res = {"given order": ic.route_sequential(grid, nets, order),
               "shortest first": ic.route_sequential(grid, nets, sorted(nets, key=lambda n: ic.md(*nets[n]))),
               "rip-up & reroute": ic.route_ripup(grid, nets, order)[0]}
        for k, routes in res.items():
            stats[k][0] += len(routes)
            stats[k][1] += len(routes) == n_nets
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.0))
    names = list(stats)
    panels = [(axes[0], [stats[k][0] for k in names], n_inst * n_nets, "Nets routed"),
              (axes[1], [stats[k][1] for k in names], n_inst, "Chips with every net routed")]
    for ax, vals, total, title in panels:
        y = np.arange(len(vals))[::-1]
        ax.barh(y, vals, color=S1, height=0.6)
        for yy, v in zip(y, vals):
            ax.text(v + total * 0.015, yy, f"{v} / {total}  ({100 * v / total:.1f}%)", va="center",
                    color=INK2, fontsize=9)
        ax.set_yticks(y, names)
        ax.tick_params(length=0, labelcolor=INK)
        ax.set_xticks([])
        for sp in ("top", "right", "bottom"):
            ax.spines[sp].set_visible(False)
        ax.set_xlim(0, total * 1.45)
        ax.set_title(title, loc="left", fontsize=10.5)
    fig.suptitle(f"Random benchmark: {n_inst} chips, 12×12 grid, {n_nets} nets, 4 random macros each",
                 x=0.02, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save(fig, "ic_benchmark.png")


def main():
    fig_maze()
    fig_river_story()
    fig_river_graph()
    fig_queens()
    fig_queens_unique()
    fig_queens_pruning()
    fig_npc()
    fig_npc_chase()
    fig_ic_single()
    fig_ic_multi()
    fig_ic_benchmark()


if __name__ == "__main__":
    main()
