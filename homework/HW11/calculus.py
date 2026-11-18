"""HW10 - Numerical differentiation and integration (數值微分與積分).

AI usage (是否使用 AI): YES. This program was written with the help of an AI
assistant (Claude Code, model Claude Opus 5.5), working from the assignment text.
本程式使用 AI（Claude Code / Claude Opus 5.5）協助撰寫。

Contents
--------
Task 1  diff(f, x)                    single-variable derivative (finite differences)
        integrate_1d(f, a, b)         single-variable integral (left / right / midpoint /
                                      trapezoid / Simpson)
Task 2  mc_integrate_1d(f, a, b)      single-variable Monte Carlo integral
Task 3  gradient(f, x)                n-variable derivative (gradient)
        integral(f, low, high)        n-variable integral / hypervolume (Riemann sum)
Task 4  mc_integral(f, low, high)     n-variable Monte Carlo integral / hypervolume
Task 5  integral(f, low, high)        Riemann integral in 1, 2, 5 and 100 dimensions
        integral_separable(...)       the same Riemann sum for f(x) = g(x_1)+...+g(x_n),
                                      computed in O(n*k) work instead of O(k^n)
Task 6  mc_integral(f, low, high)     Monte Carlo integral in 1, 2, 5 and 100 dimensions

Convention for n-variable functions
-----------------------------------
f receives points along the LAST axis: a single point has shape (n,), a batch of m
points has shape (m, n), and f returns one value per point.  Example:

    f = lambda x: np.sum(x**2, axis=-1)          # x_1^2 + ... + x_n^2

Batches make the integrals fast.  A function written for one point only, such as
``lambda x: x[0]**2 + x[1]**2``, also works if you pass ``vectorized=False`` (slower).

Run ``python calculus.py`` for the demos and ``python test_calculus.py`` for the tests.
"""
import math
import time

import numpy as np


def _evaluate(f, X, vectorized):
    """Evaluate f on every point (row) of X and return a 1-D float array."""
    if vectorized:
        return np.asarray(f(X), dtype=float).reshape(X.shape[0])
    return np.array([f(x) for x in X], dtype=float)


# =====================================================================
# Task 1 - single variable: derivative and integral
# =====================================================================
def diff(f, x, h=1e-5, method="central"):
    """Numerical derivative f'(x).

    forward  (f(x+h) - f(x)) / h          error O(h)
    backward (f(x) - f(x-h)) / h          error O(h)
    central  (f(x+h) - f(x-h)) / (2h)     error O(h^2)
    """
    if method == "forward":
        return (f(x + h) - f(x)) / h
    if method == "backward":
        return (f(x) - f(x - h)) / h
    if method == "central":
        return (f(x + h) - f(x - h)) / (2 * h)
    raise ValueError(f"unknown method {method!r}")


def integrate_1d(f, a, b, n=1000, method="midpoint", vectorized=True):
    """Numerical integral of f over [a, b] with n sub-intervals.

    left / right / midpoint are Riemann sums (error O(h), O(h), O(h^2)),
    trapezoid has error O(h^2), simpson has error O(h^4) (n is rounded up to even).
    """
    def ev(x):
        if not vectorized:
            return np.array([f(t) for t in x], dtype=float)
        return np.broadcast_to(np.asarray(f(x), dtype=float), x.shape)

    if method in ("left", "right", "midpoint"):
        h = (b - a) / n
        offset = {"left": 0.0, "right": 1.0, "midpoint": 0.5}[method]
        x = a + h * (np.arange(n) + offset)
        return float(h * np.sum(ev(x)))
    if method == "trapezoid":
        h = (b - a) / n
        y = ev(np.linspace(a, b, n + 1))
        return float(h * (np.sum(y) - (y[0] + y[-1]) / 2))
    if method == "simpson":
        if n % 2:
            n += 1
        h = (b - a) / n
        y = ev(np.linspace(a, b, n + 1))
        return float(h / 3 * (y[0] + y[-1] + 4 * np.sum(y[1:-1:2]) + 2 * np.sum(y[2:-1:2])))
    raise ValueError(f"unknown method {method!r}")


# =====================================================================
# Task 2 - single variable: Monte Carlo integral
# =====================================================================
def mc_integrate_1d(f, a, b, n=100_000, rng=None, vectorized=True):
    """Monte Carlo integral of f over [a, b].

    Draw x_1..x_n uniformly from [a, b]; then  integral ~= (b - a) * mean(f(x_i)).
    Returns (estimate, standard_error); the error shrinks like 1/sqrt(n).
    """
    rng = np.random.default_rng(rng)
    x = rng.uniform(a, b, n)
    y = np.asarray(f(x), float) if vectorized else np.array([f(t) for t in x], float)
    est = (b - a) * y.mean()
    se = (b - a) * y.std(ddof=1) / math.sqrt(n)
    return float(est), float(se)


# =====================================================================
# Task 3 - n variables: gradient (the integral is integral() below)
# =====================================================================
def gradient(f, x, h=1e-5):
    """Numerical gradient (df/dx_1, ..., df/dx_n) at point x, by central differences.

    f takes one point of shape (n,) and returns a number.
    """
    x = np.asarray(x, dtype=float)
    g = np.empty_like(x)
    for i in range(x.size):
        e = np.zeros_like(x)
        e[i] = h
        g[i] = (f(x + e) - f(x - e)) / (2 * h)
    return g


# =====================================================================
# Task 5 (also used for Task 3) - n-variable Riemann integral
# =====================================================================
def default_steps(n_dims, max_points):
    """Largest k with k**n_dims <= max_points (at least 1)."""
    k = max(1, int(math.floor(max_points ** (1.0 / n_dims) + 1e-9)))
    while k > 1 and k ** n_dims > max_points:
        k -= 1
    while (k + 1) ** n_dims <= max_points:
        k += 1
    return k


def integral(f, low, high, steps=None, method="midpoint",
             max_points=2_000_000, batch=200_000, vectorized=True):
    """Riemann integral of f over the box [low_1, high_1] x ... x [low_n, high_n].

    n = len(low).  Each axis is cut into `steps` equal pieces, so the box is cut into
    steps**n small boxes (cells).  The integral is approximated by

        sum over cells of  f(sample point of the cell) * (volume of one cell)

    with the sample point at the cell's left corner, right corner or midpoint.

    The number of cells grows as steps**n (the curse of dimensionality).  If `steps`
    is not given, the largest steps with steps**n <= max_points is used; if the given
    steps would need more than max_points cells, ValueError is raised.
    Cells are evaluated in batches of `batch` points, so memory stays small.
    """
    low = np.asarray(low, dtype=float).ravel()
    high = np.asarray(high, dtype=float).ravel()
    if low.shape != high.shape:
        raise ValueError("low and high must have the same length")
    n = low.size
    if steps is None:
        steps = default_steps(n, max_points)
    k = int(steps)
    total = k ** n                      # exact Python int, may be astronomically large
    if total > max_points:
        raise ValueError(
            f"{k}^{n} = {float(total):.3e} cells is more than max_points={max_points:,}; "
            "the Riemann sum is not feasible (curse of dimensionality)")

    offset = {"left": 0.0, "right": 1.0, "midpoint": 0.5}[method]
    h = (high - low) / k                # cell width on each axis
    cell_volume = float(np.prod(h))
    place = np.array([k ** (n - 1 - j) for j in range(n)], dtype=np.int64)  # base-k digits

    s = 0.0
    for start in range(0, total, batch):
        idx = np.arange(start, min(start + batch, total), dtype=np.int64)
        cell = (idx[:, None] // place) % k          # (m, n) integer cell coordinates
        X = low + (cell + offset) * h               # (m, n) sample points
        s += float(np.sum(_evaluate(f, X, vectorized)))
    return s * cell_volume


def integral_separable(g, low, high, steps, method="midpoint"):
    """Riemann sum of f(x) = g(x_1) + ... + g(x_n) over a box, without building the grid.

    It returns exactly the value that integral(f, low, high, steps, method) would
    return, but needs only n one-dimensional sums (O(n*k) work instead of O(k^n)):

        sum_cells sum_i g(x_i) * vol  =  sum_i [ R_i(g) * prod_{j != i} (high_j - low_j) ]

    where R_i(g) is the 1-D Riemann sum of g on axis i.  This only works because f is a
    sum of one-variable functions; a general f has no such shortcut.
    """
    low = np.asarray(low, dtype=float).ravel()
    high = np.asarray(high, dtype=float).ravel()
    lengths = high - low
    total = 0.0
    for i in range(low.size):
        r_i = integrate_1d(g, low[i], high[i], steps, method)
        total += r_i * float(np.prod(np.delete(lengths, i)))
    return total


# =====================================================================
# Task 4 / Task 6 - n-variable Monte Carlo integral
# =====================================================================
def mc_integral(f, low, high, n_samples=100_000, rng=None, batch=100_000, vectorized=True):
    """Monte Carlo integral of f over the box [low, high] (any number of dimensions).

    Draw N points uniformly in the box; integral ~= volume(box) * mean(f(points)).
    Returns (estimate, standard_error).  The error shrinks like 1/sqrt(N) whatever the
    dimension n is, which is why Monte Carlo still works in 100 dimensions.
    """
    rng = np.random.default_rng(rng)
    low = np.asarray(low, dtype=float).ravel()
    high = np.asarray(high, dtype=float).ravel()
    volume = float(np.prod(high - low))
    s = s2 = 0.0
    done = 0
    while done < n_samples:
        m = min(batch, n_samples - done)
        X = rng.uniform(low, high, size=(m, low.size))
        y = _evaluate(f, X, vectorized)
        s += float(y.sum())
        s2 += float(np.dot(y, y))
        done += m
    mean = s / n_samples
    var = max(s2 / n_samples - mean * mean, 0.0) * n_samples / (n_samples - 1)
    return volume * mean, volume * math.sqrt(var / n_samples)


# =====================================================================
# Example functions
# =====================================================================
def sum_of_squares(x):
    """f(x) = x_1^2 + ... + x_n^2  (points along the last axis)."""
    return np.sum(np.asarray(x) ** 2, axis=-1)


def unit_ball(x):
    """Indicator of the unit n-ball: 1 if x_1^2+...+x_n^2 <= 1, else 0."""
    return (np.sum(np.asarray(x) ** 2, axis=-1) <= 1.0).astype(float)


def ball_volume(n):
    """Exact volume of the unit n-ball: pi^(n/2) / Gamma(n/2 + 1)."""
    return math.pi ** (n / 2) / math.gamma(n / 2 + 1)


# =====================================================================
# Demos
# =====================================================================
def _title(text):
    print("\n" + "=" * 78)
    print(text)
    print("=" * 78)


def demo_task1():
    _title("Task 1 - single variable: derivative and integral")
    x0, exact = 1.0, math.cos(1.0)
    print(f"f(x) = sin x,  f'(1) = cos 1 = {exact:.15f}")
    print(f"{'h':>8} | {'forward error':>14} | {'central error':>14}")
    for h in [1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-8, 1e-10]:
        ef = abs(diff(math.sin, x0, h, "forward") - exact)
        ec = abs(diff(math.sin, x0, h, "central") - exact)
        print(f"{h:>8.0e} | {ef:>14.3e} | {ec:>14.3e}")
    print("Forward error ~ h, central error ~ h^2, until rounding error (~eps/h) wins.")

    print("\nf(x) = sin x on [0, pi], exact integral = 2")
    methods = ["left", "right", "midpoint", "trapezoid", "simpson"]
    print(f"{'n':>6} | " + " | ".join(f"{m:>10}" for m in methods))
    for n in [10, 100, 1000]:
        errs = [abs(integrate_1d(np.sin, 0, math.pi, n, m) - 2) for m in methods]
        print(f"{n:>6} | " + " | ".join(f"{e:>10.2e}" for e in errs))
    print("(table shows |error|; x10 more intervals -> midpoint/trapezoid x100 smaller, "
          "Simpson x10^4 smaller)")


def demo_task2():
    _title("Task 2 - single variable: Monte Carlo integral")
    print("f(x) = 4/(1+x^2) on [0, 1], exact integral = pi")
    f = lambda x: 4 / (1 + x ** 2)
    print(f"{'N':>9} | {'estimate':>10} | {'std error':>9} | {'true error':>10}")
    for n in [100, 1_000, 10_000, 100_000, 1_000_000]:
        est, se = mc_integrate_1d(f, 0, 1, n, rng=0)
        print(f"{n:>9,} | {est:>10.6f} | {se:>9.2e} | {abs(est - math.pi):>10.2e}")
    print("x100 more samples -> about x10 smaller error (1/sqrt(N)).")


def demo_task3():
    _title("Task 3 - n variables: gradient and hypervolume (numerical, Riemann)")
    f = lambda x: x[0] ** 2 * x[1] + math.sin(x[2]) + math.exp(x[0] * x[3])
    p = np.array([1.0, 2.0, 0.5, -1.0])
    exact = np.array([2 * p[0] * p[1] + p[3] * math.exp(p[0] * p[3]),
                      p[0] ** 2,
                      math.cos(p[2]),
                      p[0] * math.exp(p[0] * p[3])])
    g = gradient(f, p)
    print("f(x) = x1^2 x2 + sin x3 + exp(x1 x4)  at  x = (1, 2, 0.5, -1)")
    print("numerical gradient:", np.array2string(g, precision=10))
    print("exact gradient    :", np.array2string(exact, precision=10))
    print(f"max |error| = {np.max(np.abs(g - exact)):.2e}")

    q = np.linspace(0.1, 1.0, 10)
    print(f"\nf(x) = x1^2+...+x10^2 at x = (0.1, ..., 1.0): max |grad - 2x| = "
          f"{np.max(np.abs(gradient(sum_of_squares, q) - 2 * q)):.2e}")

    print("\nHypervolume of the unit n-ball = integral of its indicator over [-1, 1]^n")
    print(f"{'n':>2} | {'steps':>5} | {'cells':>10} | {'Riemann':>9} | {'exact':>9} | {'error':>8}")
    for n, k in [(2, 1000), (3, 100), (4, 30)]:
        v = integral(unit_ball, [-1] * n, [1] * n, steps=k)
        print(f"{n:>2} | {k:>5} | {k ** n:>10,} | {v:>9.5f} | {ball_volume(n):>9.5f} | "
              f"{abs(v - ball_volume(n)):>8.1e}")
    print("A 0/1 indicator is not smooth, so the error only falls like 1/steps.")


def demo_task4():
    _title("Task 4 - n variables: Monte Carlo hypervolume")
    N = 1_000_000
    print(f"Unit n-ball volume, N = {N:,} random points in [-1, 1]^n")
    print(f"{'n':>2} | {'MC estimate':>11} | {'std error':>9} | {'exact':>9} | {'error':>8}")
    for n in [2, 3, 4, 5, 10]:
        est, se = mc_integral(unit_ball, [-1] * n, [1] * n, N, rng=n)
        print(f"{n:>2} | {est:>11.5f} | {se:>9.1e} | {ball_volume(n):>9.5f} | "
              f"{abs(est - ball_volume(n)):>8.1e}")
    print("In 10-D the ball fills only 0.25% of the cube, so few points hit it and the")
    print("relative error grows; still, the cost per point is the same in every dimension.")


DIMS = [1, 2, 5, 100]


def demo_task5():
    _title("Task 5 - Riemann integral(f, low, high), f = x1^2+...+xn^2, low=0, high=1")
    print("exact value = n/3.  Midpoint rule with k steps gives exactly n(1/3 - 1/(12k^2)).")
    print(f"{'n':>3} | {'steps k':>7} | {'cells k^n':>10} | {'integral':>12} | {'exact':>9} | "
          f"{'error':>8} | {'time':>7}")
    for n in DIMS:
        t = time.perf_counter()
        v = integral(sum_of_squares, [0] * n, [1] * n)       # default: <= 2,000,000 cells
        t = time.perf_counter() - t
        k = default_steps(n, 2_000_000)
        print(f"{n:>3} | {k:>7} | {k ** n:>10,} | {v:>12.8f} | {n / 3:>9.5f} | "
              f"{abs(v - n / 3):>8.1e} | {t:>6.3f}s")

    print("\n5-D: the cost explodes as k^5")
    for k in [2, 4, 8, 16, 18]:
        t = time.perf_counter()
        v = integral(sum_of_squares, [0] * 5, [1] * 5, steps=k)
        t = time.perf_counter() - t
        print(f"  k = {k:>2}: {k ** 5:>9,} cells, integral = {v:.6f}, "
              f"error = {abs(v - 5 / 3):.1e}, {t:.3f}s")

    print("\n100-D: with 2,000,000 cells allowed, only k = 1 fits (one cell, the centre).")
    print("       k = 1 gives 100 * 0.5^2 = 25, far from 33.333.")
    for k in [2, 10]:
        try:
            integral(sum_of_squares, [0] * 100, [1] * 100, steps=k)
        except ValueError as err:
            print(f"  steps={k}: ValueError: {err}")
    print("  (2^100 cells at 10^9 cells/s would take about 4 * 10^13 years.)")
    print("\nBecause this f is a sum of one-variable terms, integral_separable gets the")
    print("same Riemann sum that the full k^100 grid would give, with only 100*k work:")
    for k in [1, 10, 100, 1000]:
        v = integral_separable(lambda x: x ** 2, [0] * 100, [1] * 100, k)
        print(f"  k = {k:>4}: (virtual {k}^100 cells) integral = {v:.8f}, "
              f"error = {abs(v - 100 / 3):.1e}")


def demo_task6():
    _title("Task 6 - Monte Carlo mc_integral(f, low, high), same problem")
    print(f"{'n':>3} | {'N':>9} | {'MC estimate':>12} | {'std error':>9} | {'exact':>9} | "
          f"{'error':>8} | {'time':>7}")
    for n in DIMS:
        for N in [10_000, 1_000_000]:
            t = time.perf_counter()
            est, se = mc_integral(sum_of_squares, [0] * n, [1] * n, N, rng=42)
            t = time.perf_counter() - t
            print(f"{n:>3} | {N:>9,} | {est:>12.6f} | {se:>9.1e} | {n / 3:>9.5f} | "
                  f"{abs(est - n / 3):>8.1e} | {t:>6.3f}s")
    print("Std error = sqrt(n * 4/45 / N): it grows only like sqrt(n), and 100-D costs")
    print("the same number of points as 1-D.  Riemann needs k^n cells; Monte Carlo needs N.")


def main():
    demo_task1()
    demo_task2()
    demo_task3()
    demo_task4()
    demo_task5()
    demo_task6()


if __name__ == "__main__":
    main()
