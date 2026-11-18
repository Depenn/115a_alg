# HW10 — Numerical Differentiation and Integration (數值微分與積分)

| # | Function in `calculus.py` | Method |
|---|---|---|
| 1 | `diff(f, x)`, `integrate_1d(f, a, b)` | forward / central difference; left, right, midpoint, trapezoid, Simpson |
| 2 | `mc_integrate_1d(f, a, b)` | Monte Carlo |
| 3 | `gradient(f, x)`, `integral(f, low, high)` | central difference on each axis; n-D Riemann sum |
| 4 | `mc_integral(f, low, high)` | n-D Monte Carlo |
| 5 | `integral(f, low, high)`, `integral_separable(g, low, high, k)` | n-D Riemann sum (midpoint) |
| 6 | `mc_integral(f, low, high)` | n-D Monte Carlo |

* `python calculus.py` runs the demos for all six tasks (output saved in `results.txt`).
* `python test_calculus.py` (or `pytest`) runs the tests → `all 11 tests passed`.
* Needs Python 3 and `numpy`.

---

## 0. Summary

* **Derivatives:** the central difference `(f(x+h) − f(x−h)) / 2h` has error O(h²). At
  h ≈ 1e-5 it gets about 11 correct digits. A smaller h makes it **worse**, because rounding
  error grows like ε/h.
* **1-D integrals:** for the same number of intervals, Simpson's rule is far more accurate than
  the Riemann sums: error 1e-12 against 1e-6 with 1000 intervals for ∫₀^π sin x dx.
* **Monte Carlo** error falls like **1/√N** in every dimension: 100× more points give about 10×
  less error.
* **Riemann in n dimensions** needs **kⁿ cells**. With a budget of 2,000,000 cells it is very
  accurate in 1-D and 2-D, gets about 3 digits in 5-D, and fails in 100-D: only k = 1 fits,
  and k = 2 already needs 2¹⁰⁰ ≈ 1.3·10³⁰ cells.
* **Monte Carlo in 100-D** gives 33.3330 ± 0.003 (exact 100/3 = 33.3333) with 10⁶ points
  in about 1.4 s. This is the **curse of dimensionality**: grid methods cost kⁿ,
  Monte Carlo costs N.

---

## 1. Single variable: derivative and integral (Task 1)

### 1.1 Derivative

| Formula | Name | Error |
|---|---|---|
| (f(x+h) − f(x)) / h | forward difference | O(h) |
| (f(x+h) − f(x−h)) / 2h | central difference | O(h²) |

Both come from Taylor's formula: f(x±h) = f(x) ± h f′(x) + h²/2 f″(x) ± h³/6 f‴(x) + …
In the central difference the h² terms cancel, so its error is O(h²).

**Test:** f(x) = sin x, f′(1) = cos 1 = 0.540302305868140

| h | forward error | central error |
|---|---|---|
| 1e-1 | 4.3e-2 | 9.0e-4 |
| 1e-2 | 4.2e-3 | 9.0e-6 |
| 1e-3 | 4.2e-4 | 9.0e-8 |
| 1e-4 | 4.2e-5 | 9.0e-10 |
| 1e-5 | 4.2e-6 | **1.1e-11** |
| 1e-6 | 4.2e-7 | 2.8e-11 |
| 1e-8 | 3.0e-9 | 2.6e-9 |
| 1e-10 | 5.8e-8 | 5.8e-8 |

When h is 10× smaller, the forward error is 10× smaller and the central error 100× smaller.
This holds until about h = 1e-5. Below that, f(x+h) − f(x−h) subtracts two almost equal
numbers, so rounding error (~1e-16 / h) takes over. `diff` uses h = 1e-5 by default.

### 1.2 Integral

The interval [a, b] is cut into n pieces of width h = (b − a)/n:

| Method | Formula | Error |
|---|---|---|
| left / right Riemann | h · Σ f(left or right end of each piece) | O(h) |
| midpoint Riemann | h · Σ f(middle of each piece) | O(h²) |
| trapezoid | h · [f₀/2 + f₁ + … + fₙ₋₁ + fₙ/2] | O(h²) |
| Simpson | h/3 · [f₀ + 4f₁ + 2f₂ + 4f₃ + … + fₙ] | O(h⁴) |

**Test:** ∫₀^π sin x dx = 2 (the table shows |error|)

| n | left | right | midpoint | trapezoid | Simpson |
|---|---|---|---|---|---|
| 10 | 1.65e-2 | 1.65e-2 | 8.25e-3 | 1.65e-2 | 1.10e-4 |
| 100 | 1.64e-4 | 1.64e-4 | 8.22e-5 | 1.64e-4 | 1.08e-8 |
| 1000 | 1.64e-6 | 1.64e-6 | 8.22e-7 | 1.64e-6 | 1.08e-12 |

(Left and right are only O(h) in general. Here they equal the trapezoid rule, because
sin 0 = sin π = 0.)

---

## 2. Single variable: Monte Carlo (Task 2)

Draw N random points xᵢ uniformly in [a, b]. Then

$$\int_a^b f(x)\,dx \approx (b-a)\cdot\frac{1}{N}\sum_{i=1}^{N} f(x_i), \qquad
\text{standard error} = (b-a)\,\frac{s}{\sqrt N}$$

where s is the sample standard deviation of f(xᵢ). `mc_integrate_1d` returns
`(estimate, standard_error)`.

**Test:** ∫₀¹ 4/(1+x²) dx = π (seed 0)

| N | estimate | std error | true error |
|---|---|---|---|
| 100 | 3.025961 | 6.8e-2 | 1.2e-1 |
| 1,000 | 3.104673 | 2.0e-2 | 3.7e-2 |
| 10,000 | 3.142359 | 6.4e-3 | 7.7e-4 |
| 100,000 | 3.142385 | 2.0e-3 | 7.9e-4 |
| 1,000,000 | 3.141207 | 6.4e-4 | 3.9e-4 |

The standard error goes down 10× for each 100× more points. In 1-D, Monte Carlo is much worse
than Simpson: one million points give 3–4 digits. Simpson gets 12 digits with 1000 points.

---

## 3. n variables: gradient and hypervolume (Task 3)

### 3.1 Gradient

`gradient(f, x)` applies the central difference along each axis:

$$\frac{\partial f}{\partial x_i} \approx \frac{f(x + h e_i) - f(x - h e_i)}{2h}, \quad i = 1..n$$

This needs 2n evaluations of f.

**Test 1:** f(x) = x₁²x₂ + sin x₃ + exp(x₁x₄) at x = (1, 2, 0.5, −1)

```
numerical gradient: [3.6321205588 1.           0.8775825619 0.3678794412]
exact gradient    : [3.6321205588 1.           0.8775825619 0.3678794412]
max |error| = 2.11e-11
```

**Test 2:** f(x) = x₁² + … + x₁₀² has gradient 2x. At x = (0.1, …, 1.0) the largest error is 1.8e-11.

### 3.2 Integral / hypervolume (Riemann)

`integral(f, low, high)` (described in section 5) works in any dimension. A **hypervolume** is
the integral of an indicator function: the volume of a region R is ∫ 1_R(x) dx over a box that
contains R. Example: the unit n-ball in [−1, 1]ⁿ, whose exact volume is π^{n/2} / Γ(n/2 + 1).

| n | steps per axis | cells | Riemann | exact | error |
|---|---|---|---|---|---|
| 2 | 1000 | 1,000,000 | 3.14182 | 3.14159 (π) | 2.3e-4 |
| 3 | 100 | 1,000,000 | 4.19187 | 4.18879 (4π/3) | 3.1e-3 |
| 4 | 30 | 810,000 | 4.99315 | 4.93480 (π²/2) | 5.8e-2 |

The indicator jumps from 1 to 0 at the boundary, so only the cells on the boundary are wrong.
The error therefore falls only like 1/steps, and gets worse quickly as n grows with the same
number of cells.

---

## 4. n variables: Monte Carlo hypervolume (Task 4)

`mc_integral(f, low, high, N)` draws N uniform points in the box:
integral ≈ volume(box) · mean(f). With f = indicator, this is the "fraction of points that land
inside, times the box volume".

**Test:** volume of the unit n-ball, N = 1,000,000

| n | MC estimate | std error | exact | error |
|---|---|---|---|---|
| 2 | 3.14087 | 1.6e-3 | 3.14159 | 7.2e-4 |
| 3 | 4.19180 | 4.0e-3 | 4.18879 | 3.0e-3 |
| 4 | 4.92890 | 7.4e-3 | 4.93480 | 5.9e-3 |
| 5 | 5.27110 | 1.2e-2 | 5.26379 | 7.3e-3 |
| 10 | 2.52723 | 5.1e-2 | 2.55016 | 2.3e-2 |

In 4-D, Monte Carlo with 10⁶ points (error 5.9e-3) already beats the Riemann grid with 8.1·10⁵
cells (error 5.8e-2). In 10-D the ball fills only 0.25% of the cube, so few points hit it
and the relative error grows. A grid with only 4 steps per axis would already need 4¹⁰ ≈ 10⁶ cells.

---

## 5. Riemann integral `integral(f, low, high)` in 1, 2, 5, 100 dimensions (Task 5)

### 5.1 Algorithm

```python
def integral(f, low, high, steps=None, method="midpoint", max_points=2_000_000, ...):
```

* n = `len(low)`. Each axis i is cut into k = `steps` pieces of width hᵢ = (highᵢ − lowᵢ)/k,
  so the box becomes **kⁿ cells**, each of volume h₁h₂…hₙ.
* Integral ≈ Σ over cells of f(midpoint of the cell) · (cell volume).
* Cells are numbered 0 … kⁿ − 1. Cell number c is turned into the integer coordinates
  (c₁, …, cₙ) by writing c in base k, and its midpoint is lowᵢ + (cᵢ + 0.5)·hᵢ. Cells are
  processed in batches of 200,000, so memory stays small in any dimension.
* f receives a batch of points with shape (m, n), e.g. `f = lambda x: np.sum(x**2, axis=-1)`.
  A function for one point at a time also works, with `vectorized=False`.
* If `steps` is not given, the largest k with kⁿ ≤ `max_points` (2,000,000) is used. If the
  requested k needs more cells than that, `ValueError` is raised.

**Exact answer:** for f(x) = x₁² + … + xₙ² on [0, 1]ⁿ, ∫ = n · ∫₀¹ x² dx = **n/3**. The
midpoint sum with k steps is exactly **n · (1/3 − 1/(12k²))**, and the tests check this.

### 5.2 Results (budget 2,000,000 cells)

| n | steps k | cells kⁿ | `integral` | exact n/3 | error | time |
|---|---|---|---|---|---|---|
| 1 | 2,000,000 | 2,000,000 | 0.33333333 | 0.33333 | 2.1e-14 | 0.07 s |
| 2 | 1414 | 1,999,396 | 0.66666658 | 0.66667 | 8.3e-8 | 0.15 s |
| 5 | 18 | 1,889,568 | 1.66538066 | 1.66667 | 1.3e-3 | 0.26 s |
| 100 | **1** | 1 | **25.00000000** | 33.33333 | **8.3** | 0.00 s |

5-D with more and more steps. The work grows like k⁵, while the error only falls like 1/k²:

| k | cells | integral | error |
|---|---|---|---|
| 2 | 32 | 1.562500 | 1.0e-1 |
| 4 | 1,024 | 1.640625 | 2.6e-2 |
| 8 | 32,768 | 1.660156 | 6.5e-3 |
| 16 | 1,048,576 | 1.665039 | 1.6e-3 |

### 5.3 Why 100 dimensions fails

* k = 1 is a single cell: f at the centre (0.5, …, 0.5) is 100 · 0.25 = 25.
* k = 2 needs 2¹⁰⁰ ≈ 1.27·10³⁰ cells. At 10⁹ cells per second that is about 4·10¹³ years.
  `integral` refuses it:
  `ValueError: 2^100 = 1.268e+30 cells is more than max_points=2,000,000; the Riemann sum is not feasible (curse of dimensionality)`
* k = 10 needs 10¹⁰⁰ cells, more than the number of atoms in the universe (~10⁸⁰).

So the plain Riemann sum **cannot** do the 100-D case. This is the curse of dimensionality.

**What the 100-D Riemann sum would give.** This particular f is a sum of one-variable terms,
f(x) = g(x₁) + … + g(xₙ) with g(t) = t². For such an f, the sum over all kⁿ cells reduces to
n one-dimensional sums:

$$\sum_{\text{cells}} \sum_i g(x_i)\,\Delta V = \sum_{i=1}^{n} R_i(g) \prod_{j\ne i}(\text{high}_j-\text{low}_j)$$

where Rᵢ(g) is the 1-D Riemann sum of g on axis i. `integral_separable` computes this with
only n·k work. The tests check that it equals `integral` exactly (to 1e-9) on 3-D and 4-D boxes.
It gives the value the full kⁿ grid would give:

| k | (virtual) cells | Riemann sum | error |
|---|---|---|---|
| 1 | 1 | 25.00000000 | 8.3 |
| 10 | 10¹⁰⁰ | 33.25000000 | 8.3e-2 |
| 100 | 100¹⁰⁰ | 33.33250000 | 8.3e-4 |
| 1000 | 1000¹⁰⁰ | 33.33332500 | 8.3e-6 |

This is a shortcut for this example only. A general f (for example one with products such as
x₁x₂…x₁₀₀) cannot be split this way, and then only Monte Carlo (section 6) remains.

---

## 6. Monte Carlo n-variable integral, same problem (Task 6)

`mc_integral(sum_of_squares, [0]*n, [1]*n, N)` (seed 42):

| n | N | MC estimate | std error | exact n/3 | error | time |
|---|---|---|---|---|---|---|
| 1 | 10,000 | 0.330193 | 3.0e-3 | 0.33333 | 3.1e-3 | 0.00 s |
| 1 | 1,000,000 | 0.333337 | 3.0e-4 | 0.33333 | 3.6e-6 | 0.02 s |
| 2 | 10,000 | 0.666617 | 4.2e-3 | 0.66667 | 5.0e-5 | 0.00 s |
| 2 | 1,000,000 | 0.666433 | 4.2e-4 | 0.66667 | 2.3e-4 | 0.04 s |
| 5 | 10,000 | 1.670959 | 6.7e-3 | 1.66667 | 4.3e-3 | 0.00 s |
| 5 | 1,000,000 | 1.666356 | 6.7e-4 | 1.66667 | 3.1e-4 | 0.07 s |
| 100 | 10,000 | 33.333688 | 3.0e-2 | 33.33333 | 3.6e-4 | 0.01 s |
| 100 | 1,000,000 | **33.333030** | 3.0e-3 | 33.33333 | 3.0e-4 | 1.4 s |

**Why the error does not explode with n.** Each xᵢ² (xᵢ uniform on [0, 1]) has variance
E[x⁴] − E[x²]² = 1/5 − 1/9 = 4/45. The terms are independent, so Var f = 4n/45 and

$$\text{standard error} = \sqrt{\frac{4n/45}{N}}$$

For n = 100 and N = 10⁶ this is 0.0030, matching the table. The *relative* error (error / (n/3))
even gets smaller as n grows. The tests check this formula to within 5%.

### 6.1 Riemann vs Monte Carlo

| | Riemann (grid) | Monte Carlo |
|---|---|---|
| Cost for k steps / N points | kⁿ evaluations | N evaluations |
| Error (smooth f) | midpoint: O(1/k²) = O(cells^(−2/n)) | O(1/√N), for any n |
| 1-D, 2-D | far better (1e-14, 1e-7) | 3e-4 with 10⁶ points |
| 5-D | ~1e-3 with 2·10⁶ cells | ~3e-4 with 10⁶ points |
| 100-D | impossible (k = 2 → 10³⁰ cells) | 3e-3 standard error with 10⁶ points |
| Result | deterministic | random; comes with a standard error |

The crossover is near n ≈ 4: the grid error O(cells^(−2/n)) falls more slowly than the
Monte Carlo error O(N^(−1/2)) as soon as 2/n < 1/2.

---

## 7. Tests

`python test_calculus.py` → `all 11 tests passed` (also passes under `pytest`). It checks:

* **Task 1:** `diff` is accurate to 1e-8 for sin, exp and x³. The forward error falls about 10×
  and the central error about 100× when h is 10× smaller. Midpoint on x² equals
  1/3 − 1/(12n²) exactly. Simpson is exact for cubics. `vectorized=False` works with `math.exp`.
* **Task 2:** Monte Carlo estimates for π and ∫ sin are within 4 standard errors. The standard
  error shrinks about 10× for 100× more samples. A fixed seed gives a reproducible result.
* **Task 3:** `gradient` matches the analytic gradient of the 4-variable example, and 2x for
  Σxᵢ² in 1, 2, 5 and 100 dimensions. Riemann ball volumes (2-D, 3-D) and a box volume are
  correct.
* **Task 4:** Monte Carlo ball volumes for n = 2, 3, 5 are within 4 standard errors.
* **Task 5:** `integral` gives exactly n(1/3 − 1/(12k²)) for n = 1, 2, 5, 100, and 25 for 100-D.
  Other bounds (∫∫ xy = 8) and `vectorized=False` give the same results. Left < exact < right.
  Batch size does not change the result. 2¹⁰⁰ cells raise `ValueError`.
  `integral_separable` equals the full grid for left/midpoint/right on 3-D and 4-D boxes.
* **Task 6:** for n = 1, 2, 5, 100, `mc_integral` is within 4 standard errors of n/3, and its
  standard error is within 5% of √(4n/45/N).

## 8. Limitations

* Times are from one run on one laptop. Monte Carlo results depend on the seed. Other seeds give
  different numbers with errors of the same size as the standard error.
* `integral` uses the same number of steps on every axis, and cells of equal size. Adaptive
  methods (more cells where f changes fast) and Gaussian quadrature were not implemented.
* `integral_separable` only works when f is a sum of one-variable functions. It shows what the
  100-D Riemann sum *would* be, but it is not a general 100-D integrator.
* Plain Monte Carlo was used. Variance reduction (importance sampling, stratified sampling) and
  quasi-Monte Carlo (Sobol / Halton points) would reduce the error further.
