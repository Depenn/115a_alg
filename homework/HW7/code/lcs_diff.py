"""
diff via the classic Longest-Common-Subsequence (LCS) dynamic program.

Problem
-------
Given two sequences of lines A (old file) and B (new file), produce a
minimal edit script made of deletions ("-"), insertions ("+") and
unchanged lines (" ") that turns A into B.

Dynamic-programming formulation (the textbook solution)
-------------------------------------------------------
    dp[i][j] = length of the LCS of A[:i] and B[:j]

    recurrence:
        dp[i][j] = dp[i-1][j-1] + 1          if A[i-1] == B[j-1]
        dp[i][j] = max(dp[i-1][j], dp[i][j-1])   otherwise

    base cases:
        dp[0][j] = 0 , dp[i][0] = 0

The minimal number of edits (Shortest Edit Script length) follows from
the table:   D = len(A) + len(B) - 2 * dp[len(A)][len(B)]

A traceback from dp[n][m] back to dp[0][0] recovers *which* lines were
kept / deleted / inserted.

Complexity
----------
    Time  : Theta(N * M)   (every cell is filled exactly once)
    Space : Theta(N * M)   (the whole table is needed for traceback)

Usage
-----
    python lcs_diff.py                  # small built-in demo (prints table)
    python lcs_diff.py old.txt new.txt  # diff two files
    python lcs_diff.py old.txt new.txt --table  # also print the DP table
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

# An edit-script operation: (" ", line) keep | ("-", line) delete | ("+", line) insert
Op = Tuple[str, str]


# ---------------------------------------------------------------------------
# 1. Build the DP table
# ---------------------------------------------------------------------------
def lcs_table(a: List[str], b: List[str]) -> List[List[int]]:
    """Return the (len(a)+1) x (len(b)+1) LCS length table."""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        row_prev = dp[i - 1]
        row_cur = dp[i]
        ai = a[i - 1]
        for j in range(1, m + 1):
            if ai == b[j - 1]:
                # Characters match: extend the best answer for the shorter prefixes.
                row_cur[j] = row_prev[j - 1] + 1
            else:
                # Characters differ: drop one line from A or from B, keep the better one.
                up = row_prev[j]
                left = row_cur[j - 1]
                row_cur[j] = up if up >= left else left
    return dp


# ---------------------------------------------------------------------------
# 2. Traceback the table into an edit script
# ---------------------------------------------------------------------------
def diff(a: List[str], b: List[str]) -> List[Op]:
    """Return a shortest edit script turning `a` into `b` (LCS + traceback)."""
    dp = lcs_table(a, b)
    ops: List[Op] = []

    # Walk from the bottom-right corner back to the origin.
    i, j = len(a), len(b)
    while i > 0 or j > 0:
        if (
            i > 0
            and j > 0
            and a[i - 1] == b[j - 1]
            and dp[i][j] == dp[i - 1][j - 1] + 1
        ):
            ops.append((" ", a[i - 1]))          # matched line: walk the diagonal
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or dp[i][j] == dp[i][j - 1]):
            ops.append(("+", b[j - 1]))          # insertion (came from the left)
            j -= 1
        else:
            ops.append(("-", a[i - 1]))          # deletion (came from above)
            i -= 1

    ops.reverse()
    return ops


# ---------------------------------------------------------------------------
# 3. Helpers
# ---------------------------------------------------------------------------
def format_diff(ops: List[Op]) -> str:
    return "\n".join(f"{op} {line}" for op, line in ops)


def print_table(a: List[str], b: List[str]) -> None:
    """Pretty-print the DP table (rows = A, columns = B)."""
    dp = lcs_table(a, b)
    col_w = max(4, max((len(x) for x in b), default=0) + 1)

    header = "     |" + "".join(f"{('' if c == 0 else b[c - 1]):>{col_w}}" for c in range(len(b) + 1))
    print(header)
    print("-" * len(header))
    for i in range(len(a) + 1):
        label = "" if i == 0 else a[i - 1]
        row = f"{label:>4}|" + "".join(f"{dp[i][j]:>{col_w}}" for j in range(len(b) + 1))
        print(row)


def demo() -> None:
    """Small worked example (same one used in the report)."""
    old = ["Apple", "Banana", "Cherry", "Dog"]
    new = ["Apple", "Cherry", "Dog", "Egg"]

    print("Old:", old)
    print("New:", new)
    print()
    print_table(old, new)
    print()

    ops = diff(old, new)
    print("Edit script:")
    print(format_diff(ops))

    lcs_len = lcs_table(old, new)[-1][-1]
    edits = sum(1 for op, _ in ops if op != " ")
    print()
    print(f"LCS length            = {lcs_len}")
    print(f"Shortest edit script  = {edits} "
          f"(= |A| + |B| - 2*LCS = {len(old)} + {len(new)} - 2*{lcs_len})")


# ---------------------------------------------------------------------------
# 4. CLI
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    # Don't crash on Windows consoles that use a legacy code page.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    parser = argparse.ArgumentParser(description="Textbook LCS dynamic-programming diff")
    parser.add_argument("old", nargs="?", help="old file")
    parser.add_argument("new", nargs="?", help="new file")
    parser.add_argument("--table", action="store_true",
                        help="print the DP table (only sensible for small files)")
    args = parser.parse_args(argv)

    if args.old is None or args.new is None:
        demo()
        return 0

    # utf-8-sig: strip a UTF-8 BOM if the file has one (PowerShell writes one).
    a = Path(args.old).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    b = Path(args.new).read_text(encoding="utf-8-sig", errors="replace").splitlines()

    if args.table:
        print_table(a, b)
        print()

    print(format_diff(diff(a, b)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
