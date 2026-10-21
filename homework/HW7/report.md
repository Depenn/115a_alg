# HW7 — The `diff` Problem: Dynamic Programming vs. Non-Dynamic Programming

**Problem chosen:** comparing two files to find their differences (`diff`), i.e. finding
the smallest number of changes (deleted lines and added lines) required to turn the first
file into the second file.

**Two solutions built and compared:**

| # | Approach | Algorithm | Type |
|---|------------|-----------|-------|
| A | Dynamic programming (DP) | LCS table + traceback | DP |
| B | Not dynamic programming | Myers' algorithm (1986) | Path search ordered by number of edits |

Both programs are in the `code/` folder. Both are tested to confirm they agree by
`code/test_diff.py`, and their speed is measured by `code/benchmark.py`.

---

## 0. EasySummary

* **What is `diff`?** A program that compares two versions of a file, line by line, then
  shows which lines were removed and which lines were added. It is used, for example, by
  `git` to show what changed between two versions of the code.
* **Two ways to solve it.** Approach A (DP) checks *all* possible pairs of lines from the
  two files, whatever their content. Approach B (Myers) tries from 0 changes, then 1
  change, then 2, and so on, and stops as soon as it finds the answer.
* **The results are identical.** In 428 tests, both approaches always produce the same
  minimum number of changes.
* **The difference is speed.** If the two files are almost the same (the most common
  case), approach B is **200 to 2,000 times faster**. If the two files are completely
  different, approach B is instead about **5 to 6 times slower** and uses far more memory.

---

## 1. Problem Definition

`diff` takes two lists of lines:

* the old file `A` with `N` lines,
* the new file `B` with `M` lines.

The output is the **shortest edit script** (SES), i.e. the following list of operations:

* `" "` — keep a line (that line exists in both files),
* `"-"` — delete one line from `A`,
* `"+"` — add one line from `B`.

The script must satisfy two conditions:

1. If the script is applied to `A`, the result is exactly `B`.
2. The number of `-` and `+` operations is as small as possible.

**Example.** The old file contains `Apple, Banana, Cherry, Dog`. The new file contains
`Apple, Cherry, Dog, Egg`. Its shortest script:

```
  Apple
- Banana
  Cherry
  Dog
+ Egg
```

In total 2 changes: delete `Banana`, add `Egg`.

### Relationship with LCS

**LCS** (*Longest Common Subsequence*) is the longest list of lines that appears in both
files **in the same order** (the lines need not be consecutive; what matters is that
their relative order is not reversed). In the example above, the LCS is
`Apple, Cherry, Dog`, of length 3.

The relationship to the number of changes:

* Lines that are in the LCS are kept. Their count is `L`.
* Lines of `A` outside the LCS must be deleted. Their count is `N − L`.
* Lines of `B` outside the LCS must be added. Their count is `M − L`.

So the minimum number of changes `D` is:

```
D = (N − L) + (M − L) = N + M − 2·LCS(A, B)
```

In the example: `D = 4 + 4 − 2·3 = 2`.

This means **finding a shortest edit script is the same as finding the LCS**. Therefore
the two programs below must produce the same value of `D`.

---

## 2. Approach A — Dynamic Programming (LCS Table + Traceback)

*Code: `code/lcs_diff.py`*

### 2.1 Principle

Dynamic programming (DP) breaks a big problem into small problems, stores the answer to
each small problem in a table, and reuses those answers without recomputing them. DP
fits when the problem has two properties:

* **Optimal substructure** — the best answer for a big problem is built from the best
  answers of smaller problems. Here, the LCS of `A[:i]` and `B[:j]` (the leading parts of
  both files) can be computed from the LCSs of shorter prefixes.
* **Overlapping subproblems** — the same small problem is needed many times.
  Without a table, a plain recursive LCS repeats the same computations in a number that
  grows exponentially.

**Table contents.** `dp[i][j]` = length of the LCS of the first `i` lines of file `A`
and the first `j` lines of file `B`.

**Filling rule:**

```
dp[i][j] = dp[i−1][j−1] + 1              if A[i−1] == B[j−1]   (lines match)
dp[i][j] = max(dp[i−1][j], dp[i][j−1])   if the lines differ
```

**Base values:** `dp[0][j] = dp[i][0] = 0` (if one of the files is empty, the LCS is 0).

**Working steps:**

1. **Fill the table** from top-left to bottom-right. Each cell depends only on the cell
   above it, the one to its left, and the diagonal cell to its top-left, so all values
   needed are already available when that cell is filled.
2. **Trace back** from the bottom-right cell `dp[N][M]` to the top-left cell `dp[0][0]`:
   * diagonal step → line kept,
   * step upward → line deleted,
   * step leftward → line added.

### 2.2 Worked example

Result of running `python code/lcs_diff.py` with `A = [Apple, Banana, Cherry, Dog]`
and `B = [Apple, Cherry, Dog, Egg]`:

```
     |         Apple Cherry    Dog    Egg
-----------------------------------------
    |      0      0      0      0      0
Apple|      0      1      1      1      1
Banana|      0      1      1      1      1
Cherry|      0      1      2      2      2
 Dog|      0      1      2      3      3

Edit script:
  Apple
- Banana
  Cherry
  Dog
+ Egg

LCS length            = 3
Shortest edit script  = 2 (= |A| + |B| - 2*LCS = 4 + 4 - 2*3)
```

The bottom-right number in the table (3) is the LCS length. The traceback follows the
cells `3,3 → 2,2 → 1,1 → 0,0` for the matching lines, then reports one deletion
(`Banana`) and one addition (`Egg`).

### 2.3 Why this is called DP

There is one big table full of subproblem answers. Each cell is computed exactly once
from cells that were computed earlier, and no computation is repeated. The amount of
work equals the number of cells in the table (`N × M`), **no matter how similar the two
files are**.

---

## 3. Approach B — Myers' Algorithm (Not DP)

*Code: `code/myers_diff.py`* — Eugene W. Myers, *An O(ND) Difference Algorithm and Its
Variations*, 1986. This algorithm family is used by GNU `diff` and `git diff`
(see `Referensi/AISTUDIO.md`).

### 3.1 Principle: searching by number of changes

Myers' algorithm does not fill a table of answers. It searches for a path from the start
of both files to the end of both files, and counts the number of changes used along that
path. There are three kinds of steps:

* **Lines match** — advance one line in both files. **Free** (0 changes).
* **Delete a line of `A`** — advance one line in `A` only. Cost: 1 change.
* **Add a line of `B`** — advance one line in `B` only. Cost: 1 change.

Turning `A` into `B` means finding a path from the start to the end of both files with
the smallest possible total cost. That minimum cost is `D`.

Myers searches in the following order:

```
for d = 0, 1, 2, ...                  # d = number of changes used
    for every path that uses exactly d changes:
        find the farthest position that can be reached
        (after each change, keep going forward as long as lines match)
    stop as soon as the end of both files is reached → d = D
```

The explanation:

1. First, the algorithm finds out how far it can get with **0 changes**.
   If it reaches the end of the files, it is done.
2. If it has not, it finds how far it can get with **1 change**.
3. Then 2 changes, 3 changes, and so on.
4. As soon as the end of both files is reached, the number of changes at that point is
   **guaranteed to be the smallest**, because all possibilities with fewer changes have
   already been tried and failed.

In round `d`, only about `d` paths need to be examined. Each path advances by one paid
step, then moves forward for free as long as its lines match. The total work until
completion is proportional to `N × D`.

To assemble the final script, the algorithm records the farthest position in each round,
then traces it backwards from end to start (`code/myers_diff.py: backtrack`).

### 3.2 Why this is not DP

* **There is no table of subproblem answers being reused.** The array `v[k]` only records
  the farthest position reached in the current round and is overwritten in the next
  round. Its contents are search progress, not subproblem answers stored to be used
  again.
* **The search is ordered by number of changes.** All possibilities with `d` changes are
  examined before those with `d+1`. The proof of correctness is: the first result that
  reaches the end of the files must be minimal because the cheaper ones have been
  exhausted. This is a shortest-path search on a graph, not a formula that assembles
  answers from subproblem answers.
* **The `trace` data is only a path log.** `trace` is used to walk backwards, not to
  store answers for reuse. This log can even be removed entirely: the memory-efficient
  variant used by `git` finds the script by repeatedly splitting the problem into two
  parts ("middle snake") and needs only `O(N + D)` memory. The DP table cannot be
  removed like that without losing information needed for the traceback.

---

## 4. Correctness — Both Ways Solve the Same Problem

`code/test_diff.py` checks three things on 428 inputs: 8 special cases (including empty
files, two files that share no lines at all, and files with repeated lines) plus 420
random pairs. The random pairs deliberately use a very small choice of lines so that
several equally good answers often occur.

1. **Replayable** — running the script on `A` produces exactly `B`.
2. **Minimal** — the number of changes equals `N + M − 2·LCS(A, B)`.
3. **In agreement** — the DP result and the Myers result show the same number of
   changes `D`.

```
All tests passed (428 inputs, 3 properties each).
```

Note: if there are several scripts that are equally minimal, the two programs may pick
different scripts. This is normal and harmless; the number of changes is always the
same.

---

## 5. Complexity Analysis

**Complexity** states how fast the required time or memory grows as the input gets
larger.

Meaning of the symbols:

* `N` = number of lines in the old file,
* `M` = number of lines in the new file,
* `D` = the minimum number of changes (`D = N + M − 2·LCS`). The more different the two
  files are, the larger `D` becomes.

| | **A: DP (LCS table)** | **B: Myers** |
|---|---|---|
| **Time** | `Θ(N·M)` — every table cell is filled once, always | `O(N·D)` — proportional to how *different* the two files are |
| **Memory** | `Θ(N·M)` — the whole table is kept for the traceback | `O(D²)` in this implementation (one record per round); memory-efficient variant: `O(N + D)` |
| **Best case** | `Θ(N·M)`, even for two identical files | `Θ(N)` (`D = 0`: one free advance all the way to the end) |
| **Worst case** | `Θ(N·M)` | `O(N·M)` when `D = N + M` (the two files share nothing); with the overhead in Python, measured *slower* than DP |
| **Depends on file similarity?** | No | Yes — this is its main advantage |

The core difference: **DP's time is determined by the *size* of the input, whereas
Myers' time is determined by the *difference* between the inputs.** Files that are being
edited are usually almost identical (`D` far smaller than `N`), so `O(ND)` is faster in
practice, even though its worst-case bound is the same as `Θ(NM)`.

---

## 6. Measurements (Benchmark)

How to repeat: `python code/benchmark.py`. The raw table is stored in
`code/benchmark_results.md`.

**Measurement conditions:** Python 3.10.11. For `N ≤ 1000`, the best of 3 runs; for
larger `N`, a single run. The synthetic files contain random lines that are all unique.
The `similar` scenario replaces about 1% of the lines (`D ≈ 0.02·N`).

The "Speedup" column = DP time ÷ Myers time. A number above 1 means Myers is faster;
a number below 1 means DP is faster. "n/a" means DP was not run at that size.

### 6.1 `identical` — `B` is an exact copy of `A` (D = 0)

| N (lines) | DP | Myers | Speedup (DP / Myers) | D |
|---:|---:|---:|---:|---:|
| 500 | 21.6 ms | 0.1 ms | 299.8x | 0 |
| 1,000 | 87.0 ms | 0.1 ms | 602.9x | 0 |
| 2,000 | 347.2 ms | 0.4 ms | 893.7x | 0 |
| 4,000 | 1.45 s | 0.7 ms | **2017.5x** | 0 |
| 8,000 | n/a | 1.3 ms | n/a | 0 |
| 16,000 | n/a | 2.7 ms | n/a | 0 |

DP still fills the entire `N²` table even though the two files are identical. Myers just
moves forward once from start to end, finishing in a matter of milliseconds even at
16,000 lines.

### 6.2 `similar` — `B` = `A` with ~1% of lines replaced (the common `git diff` case)

| N (lines) | DP | Myers | Speedup (DP / Myers) | D |
|---:|---:|---:|---:|---:|
| 500 | 20.3 ms | 0.1 ms | 222.6x | 10 |
| 1,000 | 87.5 ms | 0.2 ms | 438.6x | 20 |
| 2,000 | 361.2 ms | 0.7 ms | 534.9x | 40 |
| 4,000 | 1.41 s | 1.6 ms | **873.5x** | 80 |
| 8,000 | n/a | 4.2 ms | n/a | 158 |
| 16,000 | n/a | 15.8 ms | n/a | 320 |

Myers' time grows according to `N·D`, not `N²`. At 16,000 lines (`D = 320`), Myers
finishes in 15.8 ms, **about 23 times faster** than DP on a file 8 times shorter
(2,000 lines, 361.2 ms) whose table is 64 times smaller. Meanwhile, DP's time rises about
4-fold every time `N` doubles (20.3 → 87.5 → 361.2 → 1,410 ms), matching `Θ(N²)` growth.

### 6.3 `different` — the two files share no lines (D = N + M, Myers' worst case)

| N (lines) | DP | Myers | Speedup (DP / Myers) | D |
|---:|---:|---:|---:|---:|
| 250 | 4.6 ms | 29.1 ms | **0.2x** | 500 |
| 500 | 19.9 ms | 120.7 ms | **0.2x** | 1,000 |
| 1,000 | 85.6 ms | 491.2 ms | **0.2x** | 2,000 |

When no lines match, `D = N + M` and the time bound `O(ND)` becomes the same as `O(NM)`.
In this Python version, Myers becomes about 5 to 6 times **slower** than DP.

### 6.4 Peak memory (measured with `tracemalloc`)

| Scenario | N | DP | Myers |
|---|---:|---:|---:|
| identical | 2,000 | 30.7 MB | 0.0 MB |
| similar | 2,000 | 30.7 MB | 0.1 MB |
| different | 1,000 | 7.7 MB | **153.7 MB** |

The two algorithms have opposite memory patterns:

* **DP** always stores the whole `N×M` table (30.7 MB for 2,000 lines), whatever the
  files contain.
* **Myers** barely uses memory when the files are similar, but its path record grows by
  `O(D²)` when the files are very different (153.7 MB at `D = 2000`). For that reason the
  `different` scenario is only tested up to `N = 1000`, and real implementations such as
  `git` use a memory-efficient variant.

---

## 7. Comparison and Discussion

| Criteria | A: DP (LCS table) | B: Myers |
|---|---|---|
| Core idea | Fill a table of subproblem answers, then trace back | Find the shortest path ordered by number of changes, then walk it backwards |
| Principle | Optimal substructure + storing answers | Shortest path on a graph (free forward moves while lines match) |
| Time | `Θ(N·M)` always | `O(N·D)` — close to linear if the files are similar |
| Memory | `Θ(N·M)` always | `O(D²)` basic version / `O(N + D)` memory-efficient version |
| Suitable for | Small inputs, learning, and when the full LCS table is also needed | Large files with few changes — the real-world case |
| Weakness | A lot of wasted work when the files are almost identical | Slow when the files are not similar; the `D²` path record eats memory |
| Code complexity | ±45 lines, easy to establish as correct | ±75 lines, requires careful index and parity reasoning |
| Used in practice | Exercise problems (e.g. LeetCode), small tools | GNU `diff`, `git diff` (plus Patience/Histogram variants for more readable output, `Referensi/AISTUDIO.md`) |

**What those numbers show:**

1. **In real `diff` usage** (two versions of the same file), Myers is
   **200× to 2,000× faster** than DP and uses almost no memory. This is no accident of
   implementation: DP computes `N·M` cells that have nothing to do with the small
   difference between the two files, while Myers only examines the area around the best
   path.
2. **DP is easier to understand and teach.** DP shows the relationship
   `D = N + M − 2·LCS` directly, needs no complicated index reasoning, and is optimal in
   the worst case up to a constant factor. Its time bound `Θ(N·M)` is also predictable:
   worst case and typical case are the same.
3. **Myers trades a guarantee for speed.** It gives up the guarantee "time depends only
   on input size" and replaces it with "time depends on the difference between inputs".
   As a result, speed is nearly linear in the case that happens most often, at the price
   of a bad worst case (0.2x in our benchmark) and more elaborate bookkeeping.
4. **Memory is a two-way trade.** DP's memory is always `N·M`. Myers' memory is usually
   almost zero, but jumps by `D²` when the two files are completely different.

**Conclusion.** The DP solution and the non-DP solution produce **provably identical**
answers (tested on 428 inputs). Their only difference is what determines their cost: DP
is determined by the size of the files, Myers by how different the files are. For a
small-scale assignment, DP is the right choice because it is simple. For a `diff` tool on
real repositories, Myers' `O(ND)` is the reason `git diff` displays results instantly —
and that is exactly why this assignment pairs the two algorithms together.

---

## Appendix — How to Run

All commands are run from the `code/` folder (Python ≥ 3.8, standard library only):

```bash
python lcs_diff.py                   # DP demo: show the DP table + edit script
python myers_diff.py                 # demo Myers: edit script + the value D
python lcs_diff.py old.txt new.txt   # DP diff for two files (--table to print the table)
python myers_diff.py old.txt new.txt # Myers diff for two files
python test_diff.py                  # correctness tests: 428 inputs x 3 properties
python benchmark.py                  # regenerate benchmark_results.md (~1 minute)
```

File list:

| File | Purpose |
|---|---|
| `code/lcs_diff.py` | Approach A — dynamic programming |
| `code/myers_diff.py` | Approach B — non-DP (Myers `O(ND)`) |
| `code/test_diff.py` | Correctness tests (replayable, minimal, in agreement) |
| `code/benchmark.py` | Speed and memory measurement program |
| `code/benchmark_results.md` | Raw measurement tables (generated automatically) |
| `report.md` | This report |
