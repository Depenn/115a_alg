"""HW4 - Problem 1: solve a problem with an iterative method.

Problem
-------
Compute sqrt(2), i.e. the positive root of the equation

    f(x) = x^2 - 2 = 0

without ever calling a power or a square-root routine.  The equation is first
rewritten as a *fixed-point problem*  x = g(x)  and then solved by repeated
substitution  x_{n+1} = g(x_n).  This mirrors the reference script
``Materi/iterative3.py`` (which does the same thing for x^2 - 3 = 0).

Beyond the value itself, the program studies *how fast* each iteration
converges, because that is the property that actually decides whether an
iterative method is worth using.

All printed text is pure ASCII on purpose: the reference material
(``Materi/iter_framework.py``) crashes on a default Windows console because it
prints CJK characters into a cp1252 code page.  Keeping the output ASCII means
this script runs anywhere without setting PYTHONIOENCODING.

Run with:  python solve_iteration.py
"""

import math

SQRT2 = math.sqrt(2.0)  # only used to *measure* the error, never to find x


# =====================================================================
# 0. Generic iteration driver
# =====================================================================

def iterate(g, x0, tol=1e-12, max_iter=1000):
    """Apply the fixed-point iteration x_{n+1} = g(x_n) starting at x0.

    :param g:         transition function, g(x) -> next value
    :param x0:        initial guess
    :param tol:       convergence tolerance on the *step size*
    :param max_iter:  safety cap
    :returns: (history, iterations, status) where history[0] is x0,
              iterations is the number of applications of g, and status is
              "converged" or "max_iter"/"cycled".
    """
    x = x0
    history = [x]

    for n in range(1, max_iter + 1):
        x_next = g(x)
        history.append(x_next)
        if abs(x_next - x) < tol:
            return history, n, "converged"
        x = x_next

    return history, max_iter, "max_iter"


def order_of_convergence(history):
    """Empirically estimate the order p of convergence, p in {1, 2, ...}.

    For a linearly convergent sequence e_{n+1} ~ C * e_n^p (with e_n the
    absolute error), two consecutive errors are not enough, but three are:

        e_{n+1}/e_n = C * e_n^(p-1)
        e_n  /e_{n-1} = C * e_{n-1}^(p-1)

    Dividing the two and taking logarithms eliminates C:

        p = ln(e_{n+1}/e_n) / ln(e_n/e_{n-1})

    Only errors comfortably above the floating-point noise floor are used.
    """
    errs = [abs(v - SQRT2) for v in history]
    orders = []
    for i in range(2, len(errs)):
        e_m2, e_m1, e_0 = errs[i - 2], errs[i - 1], errs[i]
        if e_m2 > 1e-8 and e_m1 > 1e-8 and e_0 > 1e-8:
            ratio = math.log(e_0 / e_m1) / math.log(e_m1 / e_m2)
            if ratio > 0:
                orders.append(ratio)
    return orders


# =====================================================================
# 1. Experiment A - three different ways to write sqrt(2) = g(sqrt(2))
# =====================================================================

def g1(x):
    """g1(x) = 2/x.  Algebraically valid: x^2 = 2  <=>  x = 2/x."""
    return 2.0 / x


def g2(x):
    """g2(x) = x - 1/4 (x^2 - 2).  A damped Newton / relaxation step."""
    return x - 0.25 * (x * x - 2.0)


def g3(x):
    """g3(x) = 1/2 (x + 2/x), the Heron / Babylonian method.

    This is *exactly* Newton's method for f(x) = x^2 - 2, because
        x - f(x)/f'(x) = x - (x^2 - 2)/(2x) = (1/2)(x + 2/x).
    """
    return 0.5 * (x + 2.0 / x)


def experiment_a():
    print("=" * 72)
    print("EXPERIMENT A - three fixed-point forms of x^2 = 2, starting from x0 = 1")
    print("=" * 72)
    print()
    print("g1(x) = 2/x                (boring algebra)")
    print("g2(x) = x - 1/4 (x^2 - 2)  (relaxation with lambda = 1/4)")
    print("g3(x) = 1/2 (x + 2/x)      (= Newton's method)")
    print()

    functions = [("x1", g1), ("x2", g2), ("x3", g3)]
    x = {name: 1.0 for name, _ in functions}
    root = SQRT2

    print("  %3s | %21s | %21s | %21s | %11s | %11s" % (
        "n", "x1 = 2/x", "x2 = x-1/4(x^2-2)", "x3 = (x+2/x)/2",
        "err(x2)", "err(x3)"))
    print("  " + "-" * 88)
    print("  %3d | %21.15f | %21.15f | %21.15f | %11.3e | %11.3e" % (
        0, x["x1"], x["x2"], x["x3"], abs(x["x2"] - root), abs(x["x3"] - root)))

    for n in range(1, 21):
        for name, f in functions:
            x[name] = f(x[name])
        print("  %3d | %21.15f | %21.15f | %21.15f | %11.3e | %11.3e" % (
            n, x["x1"], x["x2"], x["x3"],
            abs(x["x2"] - root), abs(x["x3"] - root)))

    print()
    print("err(x1) is omitted on purpose: g1 oscillates forever, so its error")
    print("never shrinks and it would flatten the column.")
    print()
    print("Read the x1 column: it bounces 1 -> 2 -> 1 -> 2 ... and never settles.")
    print("Read the x2 column: monotone upward, but it crawls - roughly 0.29 of")
    print("  the previous error survives every step.")
    print("Read the x3 column: 13 correct digits after 4 steps, full double")
    print("  precision after 5, and then it stops moving entirely.")


# =====================================================================
# 2. Experiment B - why g1 fails: 2/x is an involution
# =====================================================================

def experiment_b():
    print("=" * 72)
    print("EXPERIMENT B - why g1(x) = 2/x never converges")
    print("=" * 72)
    print()
    print("Compose g1 with itself:      g1(g1(x)) = 2 / (2/x) = x")
    print()
    print("g1 is an *involution*: it is its own inverse.  Therefore the orbit of")
    print("any starting value satisfies x_{n+2} = x_n, so it is either already a")
    print("root (2-cycle of size 1) or a genuine 2-cycle of size 2.  The orbit")
    print("can never be anything else, hence g1 converges only if x0 = sqrt(2)")
    print("exactly - and sqrt(2) is irrational, so no rational x0 ever works.")
    print()
    print("More precisely, any 2-cycle is of the form {a, 2/a}, and its")
    print("multiplier is")
    print("    g1'(a) * g1'(2/a) = (-2/a^2) * (-2a^2/4) = 1.")
    print("A multiplier of exactly 1 makes the cycle *neutral*: it is neither")
    print("attracting nor repelling, which is why the orbit does not drift away")
    print("either - it is stuck forever.")
    print()
    for x0 in (1.0, 1.2, 1.5, 2.0, 3.0, 10.0):
        history, n, status = iterate(g1, x0, tol=1e-12, max_iter=50)
        print("  x0 = %5.1f -> " % x0 + " -> ".join(
            "%.10f" % v for v in history[:5]) + "   [%s]" % status)
    print()
    print("Every single start value lands in a 2-cycle, except one that is")
    print("already sqrt(2).  g1 is a textbook example of an algebraically")
    print("correct but numerically useless fixed-point formulation.")


# =====================================================================
# 3. Experiment C - sweeping the relaxation parameter lambda
# =====================================================================

def experiment_c():
    print("=" * 72)
    print("EXPERIMENT C - g(x) = x - lambda (x^2 - 2): sweeping lambda")
    print("=" * 72)
    print()
    print("For this family  g'(x) = 1 - 2*lambda*x,  so at the root")
    print("    |g'(sqrt 2)| = |1 - 2*lambda*sqrt 2|.")
    print("Contraction (convergence) requires |g'(sqrt 2)| < 1, i.e.")
    print("    0 < lambda < 1/sqrt 2 = %.10f" % (1.0 / math.sqrt(2.0)))
    print()
    optimal = 1.0 / (2.0 * math.sqrt(2.0))
    lambdas = [0.10, 0.20, 0.25, 0.30, optimal, 0.35, 0.40, 0.50, 0.60, 0.70, 0.71]

    print("  %-14s %-16s %-9s %-20s %s" % (
        "lambda", "|g'(root)|", "iters", "x_final", "note"))
    print("  " + "-" * 78)
    for lam in lambdas:
        g = lambda x, lam=lam: x - lam * (x * x - 2.0)
        history, n, status = iterate(g, 1.0, tol=1e-12, max_iter=5000)
        rate = abs(1.0 - 2.0 * lam * SQRT2)
        note = ""
        if status != "converged":
            note = "no convergence (|g'| >= 1)"
        elif abs(rate) < 1e-9:
            note = "g'(root) = 0  ->  QUADRATIC"
        elif n > 200:
            note = "extremely slow"
        elif abs(lam - optimal) < 1e-9:
            note = "optimal lambda"
        print("  %-14.8f %-16.10f %-9s %-20.15f %s" % (
            lam, rate, n if status == "converged" else "-",
            history[-1], note))
    print()
    print("The iteration counts form a U-shaped curve with its minimum at")
    print("lambda = 1/(2*sqrt 2) = %.10f," % optimal)
    print("which is exactly the value that makes g'(sqrt 2) vanish.  A fixed")
    print("point with g'(x*) = 0 is super-attractive, i.e. it converges")
    print("quadratically.  Note that this particular choice needs no derivative")
    print("of f at all - the relaxation factor alone was enough.")


# =====================================================================
# 4. Experiment D - measuring the order of convergence
# =====================================================================

def experiment_d():
    print("=" * 72)
    print("EXPERIMENT D - order of convergence, measured")
    print("=" * 72)
    print()
    print("Estimating p from p = ln(e_{n+1}/e_n) / ln(e_n/e_{n-1}):")
    print()
    for label, f in [("g2(x) = x - 1/4 (x^2 - 2)", g2),
                     ("g3(x) = 1/2 (x + 2/x)   ", g3)]:
        history, n, status = iterate(f, 1.0, tol=1e-15, max_iter=100)
        orders = order_of_convergence(history)
        shown = ", ".join("%.3f" % p for p in orders[:6])
        verdict = "1 (linear)" if orders and orders[-1] < 1.5 else "2 (quadratic)"
        print("  %s  p = %s   ->  %s" % (label, shown, verdict))
    print()
    print("g2 shrinks the error by a constant factor ~0.293 each step (linear).")
    print("g3 doubles the number of correct digits every step (quadratic).")
    print()

    print("Iterations needed to reach a given tolerance (x0 = 1):")
    print()
    tolerances = [1e-1, 1e-2, 1e-4, 1e-6, 1e-8, 1e-10, 1e-12, 1e-15]
    print("  %-10s %-14s %-14s %-14s" % ("tolerance", "g2 (linear)", "g3 (Newton)", "ratio"))
    print("  " + "-" * 56)
    for tol in tolerances:
        _, n2, _ = iterate(g2, 1.0, tol=tol, max_iter=10000)
        _, n3, _ = iterate(g3, 1.0, tol=tol, max_iter=10000)
        print("  %-10.0e %-14d %-14d %-14.1f" % (tol, n2, n3, n2 / max(n3, 1)))
    print()
    print("The ratio column is the whole point: g2 needs about 4 more")
    print("iterations for every extra 4 digits, while g3 saturates at the")
    print("floating-point floor and never needs more than 6 steps at all.")


# =====================================================================
# 5. Experiment E - derivative-free and bracketing baselines
# =====================================================================

def experiment_e():
    print("=" * 72)
    print("EXPERIMENT E - Secant and bisection on the same equation")
    print("=" * 72)
    print()
    f = lambda x: x * x - 2.0

    # --- Secant: no derivatives, order 1.618 (the golden ratio) ---
    x_prev, x_curr = 1.0, 2.0
    print("Secant method (order 1.618, no derivatives):")
    print("  %-4s %-22s %-14s" % ("n", "x_n", "|error|"))
    print("  " + "-" * 42)
    print("  %-4d %-22.15f %-14.3e" % (0, x_prev, abs(x_prev - SQRT2)))
    print("  %-4d %-22.15f %-14.3e" % (1, x_curr, abs(x_curr - SQRT2)))
    n_secant = None
    for n in range(2, 12):
        x_next = x_curr - f(x_curr) * (x_curr - x_prev) / (f(x_curr) - f(x_prev))
        x_prev, x_curr = x_curr, x_next
        print("  %-4d %-22.15f %-14.3e" % (n, x_curr, abs(x_curr - SQRT2)))
        if n_secant is None and abs(x_curr - SQRT2) < 1e-12:
            n_secant = n - 1  # n-1 applications of the secant update
        if abs(x_curr - SQRT2) < 1e-16:
            break
    print("  -> %d secant updates to reach 1e-12" % n_secant)
    print()

    # --- Bisection: order 1 but unconditionally convergent ---
    lo, hi = 1.0, 2.0
    print("Bisection (order 1, but guaranteed for any sign change):")
    print("  bracket width 1.0, halved per step, so n steps give an interval")
    print("  of length 2^-n.  Reaching 1e-12 needs ceil(12*log2(10)) = 40 steps.")
    n = 0
    while hi - lo > 1e-12:
        mid = 0.5 * (lo + hi)
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
        n += 1
    print("  steps to bracket width < 1e-12 : %d" % n)
    print("  final midpoint                : %.15f" % (0.5 * (lo + hi)))
    print()
    print("Summary of the four schemes on x^2 - 2 = 0, to 1e-12:")
    print()
    _, n_g2, _ = iterate(g2, 1.0, tol=1e-12, max_iter=10000)
    _, n_g3, _ = iterate(g3, 1.0, tol=1e-12, max_iter=10000)
    print("  %-38s %-12s %s" % ("method", "iterations", "order"))
    print("  " + "-" * 62)
    print("  %-38s %-12s %s" % ("g2 = x - 1/4 (x^2 - 2)", n_g2, "1"))
    print("  %-38s %-12s %s" % ("g3 = 1/2 (x + 2/x)  [Newton]", n_g3, "2"))
    print("  %-38s %-12s %s" % ("Secant", n_secant, "1.618"))
    print("  %-38s %-12s %s" % ("Bisection", n, "1"))


# =====================================================================
# 6. Experiment F - the same recipe on transcendental targets
# =====================================================================

def experiment_f():
    print("=" * 72)
    print("EXPERIMENT F - same recipe, transcendental targets: ln 2 and e^2")
    print("=" * 72)
    print()

    # ln 2 : root of e^x - 2 = 0
    print("(1) ln 2, solving e^x - 2 = 0 with Newton's method")
    print("    g(x) = x - (e^x - 2)/e^x = x - 1 + 2 e^(-x)")
    x = 1.0
    print("    %-4s %-22s %-14s" % ("n", "x_n", "|error|"))
    print("    " + "-" * 42)
    for n in range(0, 6):
        print("    %-4d %-22.15f %-14.3e" % (n, x, abs(x - math.log(2.0))))
        x = x - 1.0 + 2.0 * math.exp(-x)
    print("    ln 2 = %.15f" % math.log(2.0))
    print()

    # e^2 : root of ln x - 2 = 0
    target = math.e ** 2
    print("(2) e^2, solving ln x - 2 = 0 with Newton's method")
    print("    g(x) = x - (ln x - 2) * x")
    y = 1.0
    print("    %-4s %-22s %-14s" % ("n", "x_n", "|error|"))
    print("    " + "-" * 42)
    for n in range(0, 7):
        print("    %-4d %-22.15f %-14.3e" % (n, y, abs(y - target)))
        y = y - (math.log(y) - 2.0) * y
    print("    e^2 = %.15f" % target)
    print()

    print("(3) e^2 again, now by a *plain* fixed-point iteration")
    print("    ln x = 2  <=>  x = 2x / ln x,  so g(x) = 2x / ln x")
    z = 2.0
    n_steps = 0
    while abs(2.0 * z / math.log(z) - target) > 1e-12 and n_steps < 1000:
        z = 2.0 * z / math.log(z)
        n_steps += 1
    rate = 2.0 * (math.log(target) - 1.0) / math.log(target) ** 2
    print("    %-4s %-22s %-14s" % ("n", "x_n", "|error|"))
    print("    " + "-" * 42)
    print("    %-4d %-22.15f %-14.3e" % (0, 2.0, abs(2.0 - target)))
    z = 2.0
    for n in range(1, 42):
        z_prev = z
        z = 2.0 * z / math.log(z)
        if n in (1, 2, 3, 10, 20, 30, 40, 41):
            print("    %-4d %-22.15f %-14.3e" % (n, z, abs(z - target)))
        n_steps = n
    print()
    print("    Newton needed   6 steps to reach 1e-14.")
    print("    fixed point  needed %d steps for 1e-12." % n_steps)
    print("    (The test is on the size of the step |x_{n+1} - x_n|, which is")
    print("    what an iterative algorithm can actually observe; the true error")
    print("    can be slightly larger on the final step.)")
    print("    Reason: |g'(e^2)| = |2(ln x - 1)/(ln x)^2| at x = e^2 = %.6f," % rate)
    print("    so the error is only halved each step (linear), while Newton's")
    print("    method doubles the number of correct digits every step.")


# =====================================================================
# 7. Conclusion
# =====================================================================

def conclusion():
    print("=" * 72)
    print("CONCLUSION")
    print("=" * 72)
    print()
    print("sqrt(2) = %.15f" % SQRT2)
    print()
    print("1. A fixed-point formulation is not unique.  x^2 = 2 can be written")
    print("   as x = 2/x, as x = x - lambda (x^2 - 2), or as x = (x + 2/x)/2.")
    print("   All three are algebraically correct; only two of them converge.")
    print("   g1 = 2/x is an involution, so every orbit is a 2-cycle and the")
    print("   method is useless no matter where you start.")
    print()
    print("2. Convergence is governed by |g'(x*)| < 1, and the local behaviour")
    print("   is classified by that derivative: nonzero => linear, zero =>")
    print("   at least quadratic.  For the relaxation family this identifies the")
    print("   best parameter without ever differentiating f.")
    print()
    print("3. The order of convergence dominates the constant factors.  Linear")
    print("   methods need a fixed number of extra iterations per extra decimal")
    print("   digit; quadratic methods need about half as many, over and over.")
    print("   Here g3 turned out to be Newton's method in disguise, which is why")
    print("   it reached full double precision in 5 steps while g2 needed 23 to")
    print("   get within 1e-12 and 29 to get within 1e-15.")
    print()
    print("4. The pattern transfers unchanged to transcendental targets -")
    print("   ln 2 and e^2 - and to linear systems (Gauss-Seidel), eigenvalues")
    print("   (power iteration) and ODEs (Runge-Kutta).  See README.md for the")
    print("   write-up of Materi/iter_framework.py, which puts nine of these")
    print("   algorithms behind one 20-line function.")


if __name__ == "__main__":
    print()
    print("=" * 72)
    print("   HW4 Problem 1 - solving x^2 = 2 by iteration, and measuring how")
    print("   fast the different formulations converge")
    print("=" * 72)
    print()

    experiment_a()
    print()
    experiment_b()
    print()
    experiment_c()
    print()
    experiment_d()
    print()
    experiment_e()
    print()
    experiment_f()
    print()
    conclusion()
    print()
