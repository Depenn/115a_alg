"""
diff via the Myers diff algorithm (Eugene W. Myers, 1986) -- the non-DP
approach, and the one real-world tools (GNU diff, git) are built on.

Idea: edit graph, not a table
-----------------------------
Draw a grid whose x-axis is the old file A (length N) and whose y-axis is
the new file B (length M):

    right  (x+1, y)  : delete A[x]          (cost 1)
    down   (x, y+1)  : insert B[y]          (cost 1)
    diagonal (x+1,y+1): A[x] == B[y]        (cost 0, free)

Turning A into B is exactly the problem of getting from (0, 0) to (N, M)
along a path of minimum cost.  The cost of an optimal path is the length
of the Shortest Edit Script, D.

Myers searches the edit graph *outward by distance D*:

    for d = 0, 1, 2, ...            # d = number of edits used so far
        for each diagonal k = x - y in [-d, d] with the right parity:
            furthest reachable x on diagonal k after d edits
            (always take a free diagonal snake as far as it goes)

The first time (N, M) is reached, d = D is the answer, and the stored
frontier snapshots ("trace") let us walk the path backwards to recover
the concrete edit script.  Because the search is organised by *cost*
(D-paths), this is a greedy/BFS graph search -- it never fills an
overlapping-subproblem table, which is what makes it "non-DP".

Complexity
----------
    Time  : O(N * D)   (D = length of the shortest edit script)
            -> nearly linear when the files are similar (D is small),
               which is exactly the common case for `git diff`.
            -> degenerates to O(N * M) when the files are unrelated
               (then D = N + M).
    Space : O(D^2) for the naive trace kept here; git's linear-space
            refinement (divide & conquer on the "middle snake") gets
            this down to O(N + D) at the cost of a more complex
            implementation.

Usage
-----
    python myers_diff.py                  # small built-in demo
    python myers_diff.py old.txt new.txt  # diff two files
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

Op = Tuple[str, str]


# ---------------------------------------------------------------------------
# 1. Forward search: find the distance D (and keep the frontier snapshots)
# ---------------------------------------------------------------------------
def shortest_edit(a: List[str], b: List[str]) -> Tuple[List[Dict[int, int]], int]:
    """Return (trace, D): the frontier snapshots and the SES length."""
    n, m = len(a), len(b)
    max_d = n + m

    # v maps a diagonal k = x - y to the furthest x reachable on it.
    # Diagonal +1 is pre-seeded with 0 so round d = 0 can start at (0, 0).
    v: Dict[int, int] = {1: 0}
    trace: List[Dict[int, int]] = []

    for d in range(max_d + 1):
        trace.append(v.copy())          # snapshot BEFORE round d (needed to backtrack)

        for k in range(-d, d + 1, 2):
            # Come from diagonal k+1 (down = insertion) or k-1 (right = deletion)?
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                x = v[k + 1]            # moved down  -> insertion of B[y]
            else:
                x = v[k - 1] + 1        # moved right -> deletion of A[x]

            y = x - k

            # Free snake: while the lines match, slide down the diagonal at no cost.
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[k] = x

            if x >= n and y >= m:
                return trace, d

    raise RuntimeError("unreachable: max_d = N + M always suffices")


# ---------------------------------------------------------------------------
# 2. Backtrack the frontier snapshots into an edit script
# ---------------------------------------------------------------------------
def backtrack(trace: List[Dict[int, int]], a: List[str], b: List[str], d: int) -> List[Op]:
    """Walk the found path backwards from (N, M) to (0, 0)."""
    ops: List[Op] = []
    x, y = len(a), len(b)

    for step in range(d, 0, -1):
        v = trace[step]                 # frontier as it was BEFORE round `step`
        k = x - y

        # Same decision rule as the forward pass: where did we come from?
        if k == -step or (k != step and v.get(k - 1, -1) < v.get(k + 1, -1)):
            prev_k = k + 1
        else:
            prev_k = k - 1

        prev_x = v[prev_k]
        prev_y = prev_x - prev_k

        # Undo the free snake of this round (matched lines).
        while x > prev_x and y > prev_y:
            x -= 1
            y -= 1
            ops.append((" ", a[x]))

        # Undo the single paid edit of this round.
        if x > prev_x:
            x -= 1
            ops.append(("-", a[x]))     # right move = deletion
        elif y > prev_y:
            y -= 1
            ops.append(("+", b[y]))     # down move = insertion

    # Undo the free snake of round 0 (pure diagonal left over at the origin).
    while x > 0 and y > 0:
        x -= 1
        y -= 1
        ops.append((" ", a[x]))

    ops.reverse()
    return ops


# ---------------------------------------------------------------------------
# 3. Public API
# ---------------------------------------------------------------------------
def diff(a: List[str], b: List[str]) -> List[Op]:
    """Return a shortest edit script turning `a` into `b` (Myers O(ND))."""
    trace, d = shortest_edit(a, b)
    return backtrack(trace, a, b, d)


def format_diff(ops: List[Op]) -> str:
    return "\n".join(f"{op} {line}" for op, line in ops)


def demo() -> None:
    old = ["Apple", "Banana", "Cherry", "Dog"]
    new = ["Apple", "Cherry", "Dog", "Egg"]

    print("Old:", old)
    print("New:", new)
    print()

    _, d = shortest_edit(old, new)
    ops = diff(old, new)
    print("Edit script:")
    print(format_diff(ops))
    print()
    print(f"Shortest edit script = {d} "
          f"(found by exploring all paths with d < {d} edits first)")


# ---------------------------------------------------------------------------
# 4. CLI
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    # Don't crash on Windows consoles that use a legacy code page.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    parser = argparse.ArgumentParser(description="Myers O(ND) diff (non-DP)")
    parser.add_argument("old", nargs="?", help="old file")
    parser.add_argument("new", nargs="?", help="new file")
    args = parser.parse_args(argv)

    if args.old is None or args.new is None:
        demo()
        return 0

    # utf-8-sig: strip a UTF-8 BOM if the file has one (PowerShell writes one).
    a = Path(args.old).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    b = Path(args.new).read_text(encoding="utf-8-sig", errors="replace").splitlines()

    print(format_diff(diff(a, b)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
