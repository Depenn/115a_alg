# HW4 — Iterative Methods

Two problems:

| # | Task | Where the answer is |
|---|------|---------------------|
| 1 | Solve a problem of my own choosing using iteration (see `Materi/iterative3.py`) | [`solve_iteration.py`](solve_iteration.py) → [§1](#1-problem-1--finding-2-by-iteration) |
| 2 | Write a documentation file explaining `iter_framework.py` | [§2](#2-problem-2--what-iter_frameworkpy-does) |

Both are in this one file.

**Jump to:** [How to run](#how-to-run) ·
[§1 Finding √2 by iteration](#1-problem-1--finding-2-by-iteration) ·
[§2 What `iter_framework.py` does](#2-problem-2--what-iter_frameworkpy-does) ·
[What to watch out for](#things-to-be-careful-about-if-you-reuse-this)

---

## How to run

```sh
python solve_iteration.py            # Problem 1
python Materi/iter_framework.py      # Problem 2
```

**On Windows**, the second one crashes:

```
UnicodeEncodeError: 'charmap' codec can't encode characters
```

The script prints Chinese text, and the default Windows console only understands
English. Turn on UTF-8 first:

```sh
chcp 65001                                # or
$env:PYTHONIOENCODING="utf-8"             # PowerShell
```

After that all 9 demos run fine. (`solve_iteration.py` prints only English, so
it never has this problem.)

You need Python 3.10+ and NumPy.

---

## 1. Problem 1 — Finding √2 by iteration

### The idea

We want `√2`, i.e. the number where `x² = 2`.

You can't write down the answer, but you *can* rearrange the equation so it
describes itself: **"x equals some function of x"**. Then you just plug in a
guess, feed the result back in, and repeat:

```
guess  →  apply the function  →  feed back in  →  repeat until it stops changing
```

The whole problem is deciding **which function to use**. `x² = 2` can be written
several different ways, and they behave very differently.

### Three ways to write it

Starting from `x₀ = 1`:

| The function | What it does | Result |
|---|---|---|
| `g(x) = 2/x` | just rearranging the algebra | **never converges** — it just bounces between 1 and 2 forever |
| `g(x) = x − ¼(x² − 2)` | a cautious step toward the answer | works, but slowly: 23 steps |
| `g(x) = ½(x + 2/x)` | Newton's method in disguise | very fast: 6 steps |

Actual output:

```
    n |              x1 = 2/x |     x2 = x-1/4(x^2-2) |        x3 = (x+2/x)/2 |     err(x2) |     err(x3)
  ----------------------------------------------------------------------------------------
    0 |     1.000000000000000 |     1.000000000000000 |     1.000000000000000 |   4.142e-01 |   4.142e-01
    1 |     2.000000000000000 |     1.250000000000000 |     1.500000000000000 |   1.642e-01 |   8.579e-02
    2 |     1.000000000000000 |     1.359375000000000 |     1.416666666666667 |   5.484e-02 |   2.453e-03
    3 |     2.000000000000000 |     1.397399902343750 |     1.414215686274510 |   1.681e-02 |   2.124e-06
    4 |     1.000000000000000 |     1.409218280576169 |     1.414213562374690 |   4.995e-03 |   1.595e-12
    5 |     2.000000000000000 |     1.412744239998656 |     1.414213562373095 |   1.469e-03 |   2.220e-16
   ...
   20 |     2.000000000000000 |     1.414213562358354 |     1.414213562373095 |   1.474e-11 |   2.220e-16
```

Look at the three columns:

- **`x1`** goes 1, 2, 1, 2, 1, 2… It is stuck. That's not slow convergence,
  that's no convergence at all.
- **`x2`** climbs steadily toward √2 and gets there, but it creeps.
- **`x3`** is at full machine accuracy after 5 rows and then never moves again.

Final answer: **√2 = 1.414213562373095**

### Why `2/x` can never work

This one is worth understanding, because it looks like a perfectly reasonable
choice.

Feed `2/x` its own output: `2 / (2/x)` = `x`. Always. So the function is its own
reverse — apply it twice and you're back where you started. That means the
sequence can only ever be a **2-cycle**: it alternates between two values and
never gets closer to anything.

```
  starting at 1.0  ->  1.0  ->  2.0  ->  1.0  ->  2.0  ->  1.0   (forever)
  starting at 1.5  ->  1.5  ->  1.33 ->  1.5  ->  1.33 ->  1.5   (forever)
  starting at 10.0 ->  10.0 ->  0.2  ->  10.0 ->  0.2  ->  10.0  (forever)
```

The *only* start value that works is √2 itself, and √2 is irrational, so you
can never type it. This is a dead end no matter where you start from — and it's
exactly what the reference file `iterative3.py` shows with `f1 = 3/x` bouncing
between 1 and 3.

Also worth knowing: `g(x) = ½(x + 2/x)` isn't some clever trick. It **is**
Newton's method:

```
x − f(x)/f′(x)  =  x − (x² − 2)/(2x)  =  ½(x + 2/x)
```

You just didn't recognise it.

### Tuning the step size

Take the cautious version and make the step size adjustable:

```
g(x) = x − λ(x² − 2)
```

`λ` is how much of the remaining error you correct each step. Let's try a range:

| λ | steps needed |
|---|---|
| 0.10 | 79 |
| 0.25 | 23 |
| 0.30 | 16 |
| **0.35355** (= 1/(2√2)) | **5** ← best |
| 0.40 | 14 |
| 0.50 | 32 |
| 0.70 | 1308 |
| 0.71 | never converges |

The work goes **down** and then **up** again — a U shape, with the minimum right
where `λ = 1/(2√2)`.

That special value isn't a coincidence. At `λ = 1/(2√2)`, the derivative of `g`
at the answer is exactly **zero**, and a function that's flat at the point it's
converging to always converges *extra* fast. And notice what we did to find it:
**we never calculated a derivative of anything.** Just trying values of `λ`.

The lesson: at `λ = 0.71` the method is worthless, at `λ = 0.35355` it's nearly
as good as Newton's method. Same equation, same code, one number.

### How fast is "fast"?

Two ways to describe speed:

- **Linear** — every step chops off the same *fraction* of the remaining error.
  Ask for 4 more correct digits, expect a few more steps.
- **Quadratic** — every step roughly *doubles* the number of correct digits.

Measured on our two working methods (a linear method should report 1, a
quadratic one 2):

```
  g2(x) = x - 1/4 (x^2 - 2)  p = 1.185, 1.078, 1.027, 1.008, 1.002, 1.001  ->  1 (linear)
  g3(x) = 1/2 (x + 2/x)     p = 2.258, 1.984                              ->  2 (quadratic)
```

Why it matters — how many steps to reach a given accuracy:

| Accuracy wanted | `g2` (linear) | `g3` (Newton) |
|---|---|---|
| 4 digits | 8 | 4 |
| 8 digits | 16 | 5 |
| 12 digits | 23 | 6 |
| 15 digits | 29 | 6 |

`g3` never needs more than 6 steps no matter how much accuracy you ask for. It
bottoms out because the computer can't store more digits than that. `g2` keeps
paying, one step at a time, forever.

### The same race, four ways

Same equation, `x² − 2 = 0`, to 12 digits:

| Method | Steps | Speed | Needs derivatives? |
|---|---|---|---|
| `x − ¼(x² − 2)` | 23 | linear | no |
| Newton | 6 | quadratic | yes |
| Secant | 6 | in between | no |
| Bisection | 40 | linear | no, but needs a known bracket |

Secant gets Newton's accuracy without derivatives, at the cost of a weaker
guarantee. Bisection is the only one that is *guaranteed* to work as long as
you can find two points where the function changes sign.

### It works on other things too

Nothing about this recipe is specific to `√2`.

- **`ln 2`**, found as the solution of `eˣ − 2 = 0` with Newton's method from
  `x₀ = 1`: 5 steps to full accuracy.
- **`e²`**, found as the solution of `ln x − 2 = 0`, same method from `x₀ = 1`:
  6 steps.
- **`e²` again**, but this time with a plain fixed-point loop. Rearranging gives
  `x = 2x/ln x`, which is also correct — and it took **41 steps** instead of 6.

Same answer, 7× the work, because the derivative of `2x/ln x` at `e²` happens
to be exactly 0.5, so this version only ever halves the error.

### What Problem 1 shows

1. **Picking the right rearrangement is the actual work.** Three correct
   rearrangements, two work, one is hopeless.
2. **Speed comes from how the function behaves at the answer** — specifically
   whether its slope there is far from 1 (slow) or close to 0 (fast). You can
   find the good value by trial, without any calculus.
3. **The pattern is universal.** Root-finding, linear systems, eigenvalues,
   ODEs, clustering — all the same loop. Which is exactly the claim Problem 2
   is about.

---

## 2. Problem 2 — What `iter_framework.py` does

### The one big idea

Look at these problems:

- find where `x² − 2 = 0`
- solve a system of 3 linear equations
- find the biggest eigenvalue of a matrix
- integrate a differential equation
- rank web pages by popularity
- group 30 points into 2 clusters
- work out the bias of two unknown coins

They look like nine unrelated topics. They're actually the same loop nine
times:

```
make a guess  →  improve it  →  check if it's good enough  →  repeat
```

`iter_framework.py` writes that loop **once**, in a 20-line function. Each of
the nine problems is then described by just two things:

1. **How to improve the guess** (one line of code)
2. **How to decide you're done** (one line of code)

That's the entire program. Nothing clever — just refusing to write the same
loop nine times.

### The core function, with comments added

```python
def generic_iterator(transition_func,   # how to improve the guess
                     is_converged,       # how to decide we're done
                     initial_state,      # where to start
                     max_iter=1000):     # safety limit
    state = initial_state

    for iteration in range(max_iter):
        next_state = transition_func(state)          # improve it

        if is_converged(state, next_state, iteration):  # done?
            return next_state, iteration + 1

        state = next_state                             # keep it and go again

    print("  [警告] 達到最大迭代次數仍未完全收斂")   # ran out of tries
    return state, max_iter
```

That's the whole abstraction. A few things worth noticing:

- **The framework never looks inside `state`.** It doesn't know or care whether
  that's a single number, a list, a grid, or a pair. That's why the same
  function handles a `float` (Newton) and a `(time, position)` pair (Runge-Kutta)
  without a single special case.
- **`is_converged` gets both the old and the new value**, so it can measure how
  much things moved — `|new − old| < 1e-6`. That's the standard way to spot
  "it's stopped changing".
- **The iteration count is returned, not printed inside.** Each demo formats its
  own output.
- **If it runs out of tries, it says so** and returns whatever it has, rather
  than pretending to have succeeded.

### The nine demos

| # | Demo | What it solves | "Guess" is | "Done" means |
|---|---|---|---|---|
| 1 | `fixed_point` | `X = AX + b` in 2-D — the "map dropped on itself" case | a point `(x, y)` | point stopped moving |
| 2 | `newton` | `x² − 4 = 0` | one number | number stopped moving |
| 3 | `gauss_seidel` | 3 linear equations, `Ax = b` | a list of 3 numbers | numbers stopped moving |
| 4 | `power_iteration` | biggest eigenvalue of a matrix | a direction (normalised) | direction stopped turning |
| 5 | `qr_algorithm` | **all** eigenvalues of a matrix | the whole matrix | matrix stopped becoming triangular |
| 6 | `rk4` | integrate `dy/dt = y − t + 1` to `t = 2` | a pair `(time, value)` | reached time 2 |
| 7 | `pagerank` | web-page importance scores | a list of 4 scores | scores stopped moving |
| 8 | `kmeans` | split 30 points into 2 groups | 2 group centres | centres stopped moving |
| 9 | `em_two_coin` | find the bias of 2 hidden coins | 2 numbers | numbers stopped moving |

Note what stays identical and what changes:

- **Stays the same:** the loop, the call, the structure of every demo.
- **Changes:** what a "guess" happens to be (a number, a point, a list, a whole
  matrix, a time+value pair) and what counts as "done" (it stopped moving, it
  stopped changing shape, we reached the target time).

### What each demo actually computes

**1. Fixed point.** Solves `X = AX + b` where `A` shrinks everything a bit. Such
a "shrinking" map must have one point that maps to itself — that's the point
where the little map and the big map line up. Result `[0.24138, 0.896552]`
after 23 steps, matching the exact answer from linear algebra.

**2. Newton.** The familiar "walk downhill along the tangent" method, on
`x² − 4 = 0` starting from `x₀ = 1` — the worst-case midpoint between the
answer and the point where Newton breaks. It still works, in 5 steps.

**3. Gauss-Seidel.** Solves `Ax = b` by fixing one unknown at a time and
immediately reusing the value just computed. Faster than the naive version
because it never wastes work. Result `[2.25, 2, 3.75]` in 9 steps, exact.

**4. Power iteration.** Repeatedly multiply a vector by the matrix and
normalise. It naturally drifts towards the direction the matrix stretches most,
which is the dominant eigenvector; the eigenvalue is read off at the end. This is
also the practical way to get the top singular value in SVD.

**5. QR algorithm.** Repeatedly split the matrix into two factors and recombine
them in the *opposite* order. After enough rounds the matrix becomes
triangular, and its diagonal is the answer — all the eigenvalues at once,
without a separate algorithm for each one.

**6. RK4.** The standard 4th-order method for differential equations: sample the
slope in four places per step and combine them. Integrates the ODE in 10 steps.
Halving the step size cuts the error by about 16×, exactly as a 4th-order
method should.

**7. PageRank.** "A page is important if important pages link to it," modelled
as a random walk. Same iteration as demo 4, applied to the transition matrix.
Result `[0.3246, 0.2251, 0.2251, 0.2251]` — adds up to 1, as scores should.

**8. K-Means.** Repeat two steps forever: assign each point to its nearest
centre, then move each centre to the average of its points. It recovers the two
real groups exactly, in 4 rounds. (This is EM, but with a forced choice instead
of a probability — hence "hard EM".)

**9. EM, two coins.** You flip one of two coins, 10 times, 5 rounds, recording
only heads and tails — you never learn *which* coin was used. EM works in two
passes: first guess how likely each coin was behind each round, then adjust both
coins' biases using those guesses. Result `θ_A = 0.7968`, `θ_B = 0.5196`. The
guesses are sensible — the 9-heads round is 95 % likely to be coin A, the
4-heads round only 3 %.

### Output, and checking it

```
--- 1. 二維不動點迭代法 (Fixed-Point Iteration) ---
結果: [0.24138  0.896552] (耗時 23 次迭代)

--- 2. 牛頓法求根 (Newton's Method: x^2 - 4 = 0) ---
結果: 根 x = 2.000000 (耗時 5 次迭代)

--- 3. 高斯-賽得爾法 (Gauss-Seidel Linear Solver) ---
結果: x = [2.25 2.   3.75] (耗時 9 次迭代)

--- 4. 冪次迭代法 (Power Iteration: SVD / 主特徵向量) ---
結果: 最大特徵值 = 4.721570 (耗時 17 次迭代)

--- 5. QR 演算法 (QR Algorithm: 計算所有特徵值) ---
結果: 所有特徵值 = [5.732051 2.267949 1.      ] (耗時 19 次迭代)

--- 6. 龍格-庫塔法 (RK4 ODE Solver: dy/dt = y - t + 1) ---
結果: 於 t = 2.0 時, y = 9.388889 (耗時 10 步)

--- 7. PageRank (Power Iteration 隨機衝浪者模型) ---
結果: 網頁權重分佈 = [0.3246 0.2251 0.2251 0.2251] (耗時 15 次迭代)

--- 8. K-Means 聚類 (Hard EM 演算法) ---
結果: 最終分群中心 =
[[-2.1143 -2.128 ]
 [ 1.826   1.7977]] (耗時 4 次迭代)

--- 9. EM 演算法 (Two-Coin Problem 潛在變數估計) ---
結果: 估計硬幣機率 Theta_A = 0.7968, Theta_B = 0.5196 (耗時 16 次迭代)
```

I checked all nine against an independent calculation, and all nine are right.
Two are worth spelling out:

- **#6, RK4.** The ODE has an exact answer, `y = 2 + e² = 9.389056`. The
  program got `9.388889`. Not equal — but the step size is `0.2`, and RK4 makes
  errors that shrink like the fourth power of the step. Shrinking the step from
  0.4 to 0.05 (a factor of 8) cut the error from `2.3e-3` to `7.4e-7`, a factor
  of about 3000 and still climbing towards the 4096 you'd expect from 8⁴. That
  is the 4th-order behaviour working correctly, not a bug.
- **#7, PageRank.** You might expect to check this with NumPy's linear solver.
  You can't. The matrix here has a built-in eigenvalue of exactly 1 (that's what
  "scores add up to 1" means), which makes the usual linear-algebra shortcut
  singular. Asking it anyway gives you numbers around 10¹⁵ — pure rounding
  noise. The iteration isn't just convenient here, it's the only way.

### Things to be careful about if you reuse this

None of these break the demo. They're the normal gaps between a neat abstraction
and real-world use.

1. **"Moved less than 1e-6" bounds the step, not the error.** If a method is
   converging steadily but slowly, the true remaining error can be several times
   the last step. Safe enough here; dangerous when the method converges very
   slowly.
2. **Demo 4 can spin forever if the biggest eigenvalue is negative.** `v` and
   `−v` are the same direction, so the vector can flip sign every step and never
   look settled. It works in this demo only because the matrix has no negative
   entries. Comparing direction rather than sign would fix it.
3. **Demo 8 breaks on an empty group.** If every point picks the same centre,
   the other centre's average is computed over nothing, gives `nan`, and the
   loop quietly runs to the limit. Also, the starting centres are just the first
   2 rows of the data — not random. It works here; that's luck, not design.
4. **Demo 6 isn't really "converging".** Its stop test is "did we reach time 2?"
   — the right stopping rule for an ODE solver, but a different thing entirely
   from "did the answer settle". The framework accepts both, which quietly
   stretches the name `is_converged`.
5. **If a demo hits the iteration limit, it still prints a result.** The warning
   is easy to miss, so a failing run and a successful one look alike.

The through-line: the framework handles the loop so you don't have to, which
means the responsibility for *when to stop* moves entirely onto you.

### What Problem 2 shows

1. **Nine apparently different subjects, one loop.** Root-finding, linear
   systems, eigenvalues, differential equations, web ranking, clustering and
   statistics all reduce to "guess, improve, check".
2. **Two questions decide everything:** how do I improve a guess, and how do I
   know I'm finished? The framework is just those two questions with a loop
   around them.
3. **It doesn't do the thinking for you.** Every real failure mode above lives in
   the two lines the caller supplies, not in the framework.

---

## Files

```
HW4/
├── Materi/                               (given, unmodified)
│   ├── iterative3.py                     reference script for Problem 1
│   ├── iter_framework.py                 the program explained in Problem 2
│   └── [Chat Gemini] ... .md             reference material (1624 lines)
├── solve_iteration.py                    ← Problem 1
└── README.md                             ← this file
```
