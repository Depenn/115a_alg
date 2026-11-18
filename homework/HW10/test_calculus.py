"""Tests for HW10 (calculus.py).  Run: python test_calculus.py   (or: pytest)

AI usage (是否使用 AI): YES. These tests were written with the help of an AI
assistant (Claude Code, model Claude Opus 5.5).
本測試程式使用 AI（Claude Code / Claude Opus 5.5）協助撰寫。
"""
import math

import numpy as np

from calculus import (ball_volume, default_steps, diff, gradient, integral,
                      integral_separable, integrate_1d, mc_integral, mc_integrate_1d,
                      sum_of_squares, unit_ball)

DIMS = [1, 2, 5, 100]


# ---------------- Task 1 ----------------
def test_diff():
    for f, df, x in [(math.sin, math.cos, 1.0), (math.exp, math.exp, 0.3),
                     (lambda t: t ** 3, lambda t: 3 * t ** 2, -2.0)]:
        assert abs(diff(f, x) - df(x)) < 1e-8
    # central difference is exact for quadratics (up to rounding)
    assert abs(diff(lambda t: 3 * t * t - t, 2.0, h=1e-3) - 11) < 1e-9
    # forward error ~ h, central error ~ h^2
    e1 = abs(diff(math.sin, 1.0, 1e-2, "forward") - math.cos(1))
    e2 = abs(diff(math.sin, 1.0, 1e-3, "forward") - math.cos(1))
    assert 8 < e1 / e2 < 12
    c1 = abs(diff(math.sin, 1.0, 1e-2) - math.cos(1))
    c2 = abs(diff(math.sin, 1.0, 1e-3) - math.cos(1))
    assert 80 < c1 / c2 < 120


def test_integrate_1d():
    for m in ["left", "right", "midpoint", "trapezoid", "simpson"]:
        assert abs(integrate_1d(np.sin, 0, math.pi, 1000, m) - 2) < 1e-5
    # midpoint rule on x^2 over [0,1] gives exactly 1/3 - 1/(12 n^2)
    for n in [1, 3, 10, 100]:
        assert abs(integrate_1d(lambda x: x ** 2, 0, 1, n) - (1 / 3 - 1 / (12 * n * n))) < 1e-14
    # Simpson is exact for cubics
    assert abs(integrate_1d(lambda x: x ** 3 - 2 * x, -1, 2, 4, "simpson") - 0.75) < 1e-12
    # a scalar-only function with vectorized=False
    assert abs(integrate_1d(math.exp, 0, 1, 1000, "simpson", vectorized=False)
               - (math.e - 1)) < 1e-12


# ---------------- Task 2 ----------------
def test_mc_integrate_1d():
    est, se = mc_integrate_1d(lambda x: 4 / (1 + x ** 2), 0, 1, 200_000, rng=1)
    assert abs(est - math.pi) < 4 * se
    est, se = mc_integrate_1d(np.sin, 0, math.pi, 200_000, rng=2)
    assert abs(est - 2) < 4 * se
    # standard error shrinks like 1/sqrt(N)
    _, se_small = mc_integrate_1d(np.sin, 0, math.pi, 10_000, rng=3)
    _, se_big = mc_integrate_1d(np.sin, 0, math.pi, 1_000_000, rng=3)
    assert 8 < se_small / se_big < 12
    # reproducible with a seed
    assert mc_integrate_1d(np.sin, 0, 1, 1000, rng=7) == mc_integrate_1d(np.sin, 0, 1, 1000, rng=7)


# ---------------- Task 3 ----------------
def test_gradient():
    f = lambda x: x[0] ** 2 * x[1] + math.sin(x[2]) + math.exp(x[0] * x[3])
    p = np.array([1.0, 2.0, 0.5, -1.0])
    exact = [2 * p[0] * p[1] + p[3] * math.exp(p[0] * p[3]), p[0] ** 2,
             math.cos(p[2]), p[0] * math.exp(p[0] * p[3])]
    assert np.allclose(gradient(f, p), exact, atol=1e-8)
    rng = np.random.default_rng(0)
    for n in [1, 2, 5, 100]:
        x = rng.uniform(-2, 2, n)
        assert np.allclose(gradient(sum_of_squares, x), 2 * x, atol=1e-8)


def test_riemann_hypervolume():
    assert abs(integral(unit_ball, [-1, -1], [1, 1], steps=1000) - math.pi) < 1e-3
    assert abs(integral(unit_ball, [-1] * 3, [1] * 3, steps=100) - 4 * math.pi / 3) < 1e-2
    # box volume = integral of 1
    one = lambda X: np.ones(len(X))
    assert abs(integral(one, [0, -1, 2], [2, 1, 5], steps=4) - 12) < 1e-12


# ---------------- Task 4 ----------------
def test_mc_hypervolume():
    for n in [2, 3, 5]:
        est, se = mc_integral(unit_ball, [-1] * n, [1] * n, 400_000, rng=n)
        assert abs(est - ball_volume(n)) < 4 * se


# ---------------- Task 5 ----------------
def test_integral_dims():
    # midpoint Riemann sum of x1^2+..+xn^2 on [0,1]^n with k steps = n(1/3 - 1/(12k^2))
    for n in DIMS:
        k = default_steps(n, 2_000_000)
        v = integral(sum_of_squares, [0] * n, [1] * n)
        assert abs(v - n * (1 / 3 - 1 / (12 * k * k))) < 1e-9
    assert abs(integral(sum_of_squares, [0], [1]) - 1 / 3) < 1e-10
    assert abs(integral(sum_of_squares, [0] * 2, [1] * 2) - 2 / 3) < 1e-6
    assert abs(integral(sum_of_squares, [0] * 5, [1] * 5) - 5 / 3) < 2e-3
    assert integral(sum_of_squares, [0] * 100, [1] * 100) == 25.0   # only k = 1 fits


def test_integral_general():
    # non-unit, non-equal bounds:  int_1^3 int_0^2 x*y dy dx = 4 * 2 = 8 (midpoint exact)
    assert abs(integral(lambda X: X[:, 0] * X[:, 1], [1, 0], [3, 2], steps=5) - 8) < 1e-12
    # a one-point function with vectorized=False gives the same answer
    g = lambda x: x[0] ** 2 + x[1] ** 2 + x[2] ** 2
    a = integral(g, [0, 0, 0], [1, 2, 3], steps=6, vectorized=False)
    b = integral(sum_of_squares, [0, 0, 0], [1, 2, 3], steps=6)
    assert abs(a - b) < 1e-9
    # left / right sums bracket the integral of an increasing function
    lo = integral(sum_of_squares, [0] * 3, [1] * 3, steps=10, method="left")
    hi = integral(sum_of_squares, [0] * 3, [1] * 3, steps=10, method="right")
    assert lo < 1 < hi
    # batching does not change the result
    assert abs(integral(sum_of_squares, [0] * 4, [1] * 4, steps=9, batch=7)
               - integral(sum_of_squares, [0] * 4, [1] * 4, steps=9)) < 1e-12


def test_integral_too_many_cells():
    try:
        integral(sum_of_squares, [0] * 100, [1] * 100, steps=2)
    except ValueError:
        pass
    else:
        raise AssertionError("2^100 cells should be refused")


def test_separable_matches_full_grid():
    for method in ["left", "midpoint", "right"]:
        for low, high, k in [([0, 0, 0], [1, 1, 1], 7), ([-1, 0, 2, 1], [1, 3, 4, 1.5], 5)]:
            full = integral(sum_of_squares, low, high, steps=k, method=method)
            fast = integral_separable(lambda x: x ** 2, low, high, k, method)
            assert abs(full - fast) < 1e-9
    v = integral_separable(lambda x: x ** 2, [0] * 100, [1] * 100, 1000)
    assert abs(v - 100 * (1 / 3 - 1 / 12e6)) < 1e-9


# ---------------- Task 6 ----------------
def test_mc_integral_dims():
    for n in DIMS:
        est, se = mc_integral(sum_of_squares, [0] * n, [1] * n, 200_000, rng=n)
        assert abs(est - n / 3) < 4 * se
        # theory: Var(x^2) = 1/5 - 1/9 = 4/45 per coordinate
        assert abs(se / math.sqrt(n * 4 / 45 / 200_000) - 1) < 0.05
    a = mc_integral(sum_of_squares, [0] * 5, [1] * 5, 1000, rng=9)
    b = mc_integral(sum_of_squares, [0] * 5, [1] * 5, 1000, rng=9)
    assert a == b


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"all {len(tests)} tests passed")
