# HW5 — Recursion, Functional Programming, Lambda Calculus

Week 5 homework, issue #7. Three problems:

| # | Problem | File |
|---|---------|------|
| 1 | Tower of Hanoi, solved **with** recursion **and** without recursion | [`hanoi.py`](hanoi.py) |
| 2 | Symbolic differentiation `sym_diff(expr)`, solved recursively | [`sym_diff.py`](sym_diff.py) |
| 3 | Hand-built `map`, `filter`, `reduce` + bubble sort **without any loop** | [`func_bubble.py`](func_bubble.py) |

**Jump to:** [How to run](#how-to-run) ·
[1. Tower of Hanoi](#1-tower-of-hanoi) ·
[2. Symbolic differentiation](#2-symbolic-differentiation-sym_diffexpr) ·
[3. Functional bubble sort](#3-functional-bubble-sort) ·
[Things to be careful about](#things-to-be-careful-about)

---

## How to run

```sh
python hanoi.py        # Problem 1
python sym_diff.py     # Problem 2
python func_bubble.py  # Problem 3
```

You need Python 3.10+; no third-party packages.

---

## 1. Tower of Hanoi

### The problem

Three pegs `A`, `B`, `C` and `n` discs of decreasing size. Rules:

- move one disc at a time,
- a larger disc may never sit on a smaller one.

Goal: move the whole stack from `A` to `C`. The classic minimal solution needs
`2ⁿ − 1` moves, and the recursive structure is the reason *why*:

```
to move n discs   : move n-1 discs aside, move the big one, move n-1 back
to move n-1 discs : move n-2 discs aside, move that one, move n-2 back
...
```

Each level just reuses the same recipe at a smaller size — recursion.

### Three implementations

`hanoi.py` solves it three ways and prints all move sequences side by side:

| Function | Technique |
|---|---|
| `solve_recursive` | Direct recursion: the recipe above. |
| `solve_stack` | **No recursion.** Emulates the call stack manually — a `while` loop pops a frame, and a "phase" flag tells it whether to recurse, move the disc, or unwind. Same shape as the recursion, no function calling itself. |
| `solve_iterative` | **No recursion.** The classic cyclic algorithm: the smallest disc cycles through the pegs (direction depends on whether `n` is even or odd), and on alternate moves the two pegs that *aren't* holding the smallest disc do their one legal move. Total `2ⁿ − 1` moves. |

### Output and verification

```
=== Hanoi n = 3 (moves = 7, expected 2^3-1 = 7) ===
  recursive  : A->C -> A->B -> C->B -> A->C -> B->A -> B->C -> A->C
  stack      : A->C -> A->B -> C->B -> A->C -> B->A -> B->C -> A->C
  iterative  : A->C -> A->B -> C->B -> A->C -> B->A -> B->C -> A->C
  all identical & count OK: True
```

The program checks, for `n = 3` and `n = 4`, that all three methods produce the
*identical* move sequence and that the length is exactly `2ⁿ − 1`.

---

## 2. Symbolic differentiation (`sym_diff(expr)`)

### The problem

Given a mathematical expression, return its derivative **as an expression**,
not as a number:

```
d/dx (x^3 + 2*x)   ->   3*x^2 + 2
```

This is a structural problem, and structure is exactly what recursion handles:
an expression *is* a tree, and the derivative of a node is a combination of the
derivatives of its children.

### The pipeline

`sym_diff.py` turns a string into a tree, differentiates, cleans up, and prints:

```
"x^3 + 2*x"
  --parse-->  ('+' , ('^','x',3) , ('*',2,'x'))     # an AST
  --diff--->  ('+' , ('*',3,('^','x',2)) , 2)        # recursive rule engine
  --simplify-> ('+' , ('*',3,('^','x',2)) , 2)       # 0*z=0, 1*z=z, 0+z=z, ...
  --to_str-->  "3 * x^2 + 2"
```

- **Parser** — recursive-descent. Operators `+ - * / ^`, unary minus,
  parentheses, and functions `sin cos exp ln`. (`**` is accepted as `^`.)
- **`diff(expr)`** — recursive. One rule per node type:

  | Expression | Derivative |
  |---|---|
  | constant `c` | `0` |
  | `x` | `1` |
  | `u + v`, `u − v` | `du + dv`, `du − dv` |
  | `u * v` | `du*v + u*dv` (product rule) |
  | `u / v` | `(du*v − u*dv) / v²` (quotient rule) |
  | `u^v` | `v*u^(v−1)*du + u^v*ln(u)*dv` (general power rule) |
  | `sin(u)`, `cos(u)` | `cos(u)*du`, `−sin(u)*du` |
  | `exp(u)`, `ln(u)` | `exp(u)*du`, `du/u` |

  The `u^v` rule is the bonus that makes even `x^x` work: the second term dies
  whenever the exponent is a constant, because its derivative is `0`.
- **`simplify(expr)`** — recursively folds `0±x`, `x±0`, `0*x`, `1*x`, `0/…`,
  `x/1`, `x^0`, `x^1` and numeric constants, so the printed result is compact.
- **`evaluate(expr, x)`** — evaluates an AST at a number, used for testing.

### Output and verification

```
  f(x)  = (x^2 + 1) / (x - 1)
  f'(x) = (2 * x * (x - 1) - (x^2 + 1)) / (x - 1)^2
  f'(0.7) analytic = -21.2222222222 | numeric = -21.2222222231 | rel.err = 4.21e-11
```

Every example is checked two independent ways: the symbolic derivative evaluated
at `x = 0.7` is compared with a central finite difference
`(f(x+h) − f(x−h)) / 2h`. The relative error is ~10⁻¹¹ in every case — the two
calculations agree.

Six built-in examples: `x^3 + 2*x`, `sin(x) * x^2 + exp(x)`,
`(x^2 + 1) / (x - 1)`, `cos(2*x)`, `ln(x) + 1/x`, and `x^x`.

---

## 3. Functional bubble sort

### The problem

Three commands, all from the functional-programming toolbox:

1. Build **your own** `map`, `filter`, `reduce` (not the built-ins).
2. Use them to implement bubble sort.
3. **No `for`, no `while` — anywhere.** Everything is recursion and composition.

Those three functions are the classic recursive list-processing trio:

```
my_map(f, [a,b,c])     = [f(a), f(b), f(c)]            # transform each element
my_filter(p, [a,b,c])  = [a, c]                        # keep the ones where p holds
my_reduce(f, [a,b,c], 0) = f(f(f(0, a), b), c)         # fold the whole list into one value
```

`map` = recursion over the head, `filter` = recursion that drops the head when
the test fails, `reduce` = recursion that carries the accumulated value in the
arguments. All three are five-line functions. No loops required.

### Bubble sort on top of them

Bubble sort = "repeatedly sweep the list, carrying the largest element to the
right". The sweep — `bubble_pass` — is a **reduce**:

```python
def sift(acc, x):              # one comparison step of a sweep
    if acc == [] or last(acc) <= x:
        return acc + [x]       # already in order, append x
    return init(acc) + [x, last(acc)]   # x < last(acc) -> swap them

def bubble_pass(xs):
    return my_reduce(sift, xs, [])      # largest element now sits at the right end
```

The full sort removes the (now correct) last element and sorts the prefix
recursively:

```python
def bubble_sort(xs):
    if tail(xs) == []:
        return xs
    passed = bubble_pass(xs)
    return bubble_sort(init(passed)) + [last(passed)]
```

### Output and verification

```
  one bubble_pass [3, 5, 2, 4, 1]  = [3, 2, 4, 1, 5]   (largest -> right end)
  bubble_sort     [3, 5, 2, 4, 1]  = [1, 2, 3, 4, 5]
  is_sorted(result)          = True
  equal to built-in sorted() = True
```

Note it even uses its own functions to *verify* itself: `is_sorted` builds the
list of neighbouring pairs and folds them with `and` using `my_map` +
`my_reduce`. Extra test cases, including an empty list and one with duplicates,
all pass.

---

## Things to be careful about

1. **Python's recursion limit.** `hanoi.py` runs `n = 3, 4` only; the recursive
   solver would exceed the default 1000-frame limit around `n = 500`. The two
   non-recursive methods are unaffected.
2. **`^` vs `**`.** In Python, `^` is *XOR* — so `sym_diff.py` parses it itself
   (both `^` and `**` are accepted) and never relies on Python's meaning.
3. **Symbolic soup.** Simplification is deliberately small (`0*x`, `1*x`, …).
   The general power rule can leave expressions that are *correct but not the
   textbook form*; the numeric check is what confirms they're equivalent.
4. **The fold is lazy.** The simplifier folds two numbers with a chain of
   `if/elif`, never by building a `dict` of all operators — otherwise Python
   would evaluate every result eagerly and crash on a harmless `1/0` inside a
   `-` node. (This was a real bug during development.)
5. **`func_bubble.py` pays performance for purity.** No loops means the list is
   rebuilt constantly (`acc + [x]`, `init(passed) + […]`), so the sort is
   O(n³)-ish. It's a demonstration of style, not speed.

---

## Files

```
HW5/
├── hanoi.py         ← Problem 1 (3 implementations + verification)
├── sym_diff.py      ← Problem 2 (parser + recursive diff + numeric check)
├── func_bubble.py   ← Problem 3 (self-made map/filter/reduce, loop-free sort)
└── README.md        ← this file
```