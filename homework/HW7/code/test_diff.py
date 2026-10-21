"""
Correctness tests for the two diff implementations.

Properties checked on every input (fixed edge cases + hundreds of random
pairs with deliberately tiny alphabets to force many ties):

    1. Replayability : applying the edit script to A reconstructs B exactly.
    2. Minimality    : the number of edits equals the theoretical optimum
                       D = |A| + |B| - 2 * LCS(A, B).
    3. Agreement     : the DP diff and the Myers diff agree on D.

Run:  python test_diff.py
"""

import random

from lcs_diff import diff as lcs_diff_ops
from lcs_diff import lcs_table
from myers_diff import diff as myers_diff_ops


def replay(a, ops):
    """Apply an edit script to `a`; return the reconstructed sequence."""
    out = []
    i = 0
    for op, line in ops:
        if op == " ":
            assert i < len(a) and a[i] == line, f"keep mismatch at index {i}"
            out.append(a[i])
            i += 1
        elif op == "-":
            assert i < len(a) and a[i] == line, f"delete mismatch at index {i}"
            i += 1
        elif op == "+":
            out.append(line)
        else:
            raise AssertionError(f"unknown op {op!r}")
    assert i == len(a), "edit script did not consume all of A"
    return out


def edits(ops):
    return sum(1 for op, _ in ops if op != " ")


def check(a, b, label):
    lcs_len = lcs_table(a, b)[-1][-1]
    optimum = len(a) + len(b) - 2 * lcs_len

    dp_ops = lcs_diff_ops(a, b)
    my_ops = myers_diff_ops(a, b)

    assert replay(a, dp_ops) == b, f"{label}: DP script does not replay to B"
    assert replay(a, my_ops) == b, f"{label}: Myers script does not replay to B"
    assert edits(dp_ops) == optimum, \
        f"{label}: DP used {edits(dp_ops)} edits, optimum is {optimum}"
    assert edits(my_ops) == optimum, \
        f"{label}: Myers used {edits(my_ops)} edits, optimum is {optimum}"
    return optimum


def fixed_cases():
    cases = [
        ([], [], "both empty"),
        (["x"], [], "delete everything"),
        (["x", "y", "z"], [], "delete everything (longer)"),
        ([], ["x"], "insert everything"),
        (["a"], ["a", "b", "a"], "insert with repeats"),
        (["same"] * 5, ["same"] * 5, "identical"),
        (["Apple", "Banana", "Cherry", "Dog"],
         ["Apple", "Cherry", "Dog", "Egg"], "report demo"),
        ("the quick brown fox jumps over the lazy dog".split(),
         "the quick red fox leaps over a lazy dog".split(), "sentence edit"),
    ]
    for a, b, label in cases:
        d = check(a, b, label)
        print(f"  ok  {label:28s} |A|={len(a):2d} |B|={len(b):2d} D={d}")
    return len(cases)


def random_cases(trials=400):
    rng = random.Random(20261021)
    for t in range(trials):
        # Tiny alphabets -> lots of repeated lines -> lots of tie-breaking.
        alpha = rng.randint(1, 4)
        pool = [f"w{j}" for j in range(alpha)]
        n = rng.randint(0, 12)
        m = rng.randint(0, 12)
        a = [rng.choice(pool) for _ in range(n)]
        b = [rng.choice(pool) for _ in range(m)]
        check(a, b, f"random#{t}")
    for t in range(20):
        # A few larger pairs over a bigger alphabet.
        pool = [f"line-{j}" for j in range(30)]
        n = rng.randint(0, 60)
        m = rng.randint(0, 60)
        a = [rng.choice(pool) for _ in range(n)]
        b = [rng.choice(pool) for _ in range(m)]
        check(a, b, f"random-large#{t}")
    print(f"  ok  {trials + 20} randomised pairs")


def main():
    total = 0
    print("Fixed edge cases:")
    total += fixed_cases()
    print("Randomised property tests:")
    random_cases()
    total += 420
    print(f"\nAll tests passed ({total} inputs, 3 properties each).")


if __name__ == "__main__":
    main()
