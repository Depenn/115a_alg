"""Problem 3 - Eight queens, solved with DFS + backtracking.

Place 8 queens on an 8x8 board so that no two share a row, column or diagonal.

The search tree: level r = "which column does the queen in row r go to?".
DFS fills one row at a time; as soon as a partial placement has a conflict the
whole subtree below it is skipped (pruning) and the search backtracks.

Conflict test in O(1): keep three sets
    cols    - used columns
    diag1   - used (r - c)   (top-left to bottom-right diagonals)
    diag2   - used (r + c)   (top-right to bottom-left diagonals)
"""
import time


def solve_queens(n=8, first_only=False):
    """Return (list_of_solutions, nodes_visited). A solution is a tuple: sol[row] = column."""
    solutions = []
    cols, diag1, diag2 = set(), set(), set()
    placement = []
    nodes = 0

    def place(r):
        nonlocal nodes
        if r == n:
            solutions.append(tuple(placement))
            return first_only
        for c in range(n):
            nodes += 1
            if c in cols or (r - c) in diag1 or (r + c) in diag2:
                continue                       # prune: conflict
            cols.add(c); diag1.add(r - c); diag2.add(r + c); placement.append(c)
            if place(r + 1):
                return True
            cols.remove(c); diag1.remove(r - c); diag2.remove(r + c); placement.pop()
        return False

    place(0)
    return solutions, nodes


def brute_force_count(n=8):
    """For comparison: try every placement with one queen per row (n^n leaves), no pruning."""
    from itertools import product
    count = 0
    for cand in product(range(n), repeat=n):
        if is_valid(cand):
            count += 1
    return count


def is_valid(sol):
    n = len(sol)
    for i in range(n):
        for j in range(i + 1, n):
            if sol[i] == sol[j] or abs(sol[i] - sol[j]) == j - i:
                return False
    return True


def canonical(sol):
    """Smallest representative under the 8 board symmetries (rotations + reflections)."""
    n = len(sol)
    cells = {(r, c) for r, c in enumerate(sol)}
    forms = []
    for _ in range(4):
        cells = {(c, n - 1 - r) for r, c in cells}                # rotate 90 degrees
        for variant in (cells, {(r, n - 1 - c) for r, c in cells}):  # and mirror
            forms.append(tuple(c for r, c in sorted(variant)))
    return min(forms)


def board(sol):
    n = len(sol)
    return "\n".join(" ".join("Q" if sol[r] == c else "." for c in range(n)) for r in range(n))


def main():
    t = time.perf_counter()
    sols, nodes = solve_queens(8)
    dt = time.perf_counter() - t
    first, first_nodes = solve_queens(8, first_only=True)
    unique = {canonical(s) for s in sols}

    print("=== Eight queens (DFS + backtracking) ===")
    print(f"all solutions          : {len(sols)}  ({nodes} column tries, {dt * 1000:.1f} ms)")
    print(f"distinct up to symmetry: {len(unique)}")
    print(f"first solution found after {first_nodes} column tries: {first[0]}")
    print(board(first[0]))
    print(f"all valid: {all(is_valid(s) for s in sols)}")
    print(f"brute force would test 8^8 = {8 ** 8} placements")

    print("\nn-queens counts with the same DFS:")
    for n in range(4, 11):
        s, k = solve_queens(n)
        print(f"  n={n:2d}: {len(s):4d} solutions, {k:7d} column tries")


if __name__ == "__main__":
    main()
