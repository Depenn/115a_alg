"""Problem 1 - Rat in a maze, solved with Depth-First Search (DFS).

The rat starts at 'S' and must reach 'E'. '#' is a wall, '.' is open floor.
DFS walks as deep as possible in one direction and backtracks when it hits
a dead end.  Two versions are given:

* dfs_recursive  - classic backtracking (the call stack is the DFS stack)
* dfs_iterative  - the same search with an explicit stack

For comparison, bfs_shortest finds the shortest path, to show that the path
DFS returns is *a* path but not necessarily the shortest one.
"""
from collections import deque

MAZE_TEXT = """\
###########
#S....#...#
#.###.#.#.#
#.#...#.#.#
#.#.###.#.#
#.#.....#.#
#.#####.#.#
#.......#.#
#####.###.#
#E........#
###########"""

# Search order: right, down, left, up
DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def parse(text):
    grid = [list(row) for row in text.splitlines()]
    start = end = None
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == "S":
                start = (r, c)
            elif ch == "E":
                end = (r, c)
    return grid, start, end


def neighbours(grid, cell):
    r, c = cell
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != "#":
            yield (nr, nc)


def dfs_recursive(grid, start, end):
    """Backtracking DFS. Returns (path, number_of_cells_visited)."""
    visited = set()
    path = []

    def go(cell):
        visited.add(cell)
        path.append(cell)              # step forward
        if cell == end:
            return True
        for nxt in neighbours(grid, cell):
            if nxt not in visited and go(nxt):
                return True
        path.pop()                     # dead end -> backtrack
        return False

    found = go(start)
    return (path if found else None), visited


def dfs_iterative(grid, start, end):
    """DFS with an explicit stack; parent links rebuild the path."""
    stack = [start]
    parent = {start: None}
    visited = set()
    while stack:
        cell = stack.pop()
        if cell in visited:
            continue
        visited.add(cell)
        if cell == end:
            path = []
            while cell is not None:
                path.append(cell)
                cell = parent[cell]
            return path[::-1], len(visited)
        # push in reverse so the first direction in DIRS is explored first
        for nxt in reversed(list(neighbours(grid, cell))):
            if nxt not in visited:
                parent[nxt] = cell
                stack.append(nxt)
    return None, len(visited)


def bfs_shortest(grid, start, end):
    parent = {start: None}
    q = deque([start])
    while q:
        cell = q.popleft()
        if cell == end:
            break
        for nxt in neighbours(grid, cell):
            if nxt not in parent:
                parent[nxt] = cell
                q.append(nxt)
    if end not in parent:
        return None
    path, cell = [], end
    while cell is not None:
        path.append(cell)
        cell = parent[cell]
    return path[::-1]


def draw(grid, path, visited=()):
    """'*' = final path, 'x' = visited by DFS but abandoned (backtracked)."""
    g = [row[:] for row in grid]
    for r, c in visited:
        if g[r][c] == ".":
            g[r][c] = "x"
    for r, c in path[1:-1]:
        g[r][c] = "*"
    return "\n".join("".join(row) for row in g)


def main():
    grid, start, end = parse(MAZE_TEXT)
    path, visited = dfs_recursive(grid, start, end)
    path2, visited2 = dfs_iterative(grid, start, end)
    shortest = bfs_shortest(grid, start, end)

    print("=== Rat in a maze (DFS) ===")
    print(f"start={start} end={end}")
    print(f"recursive DFS : {len(path) - 1} steps, {len(visited)} cells visited")
    print(f"iterative DFS : {len(path2) - 1} steps, {visited2} cells visited")
    print(f"BFS (shortest): {len(shortest) - 1} steps")
    print("\nDFS path ('*' = path, 'x' = dead end, backtracked):")
    print(draw(grid, path, visited))
    print("\nBFS shortest path ('*'):")
    print(draw(grid, shortest))


if __name__ == "__main__":
    main()
