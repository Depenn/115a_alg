"""
Traveling Salesman Problem (TSP) - five methods on the same test data.

1. Improvement method (2-opt, best-improvement, starts from the greedy tour)
2. Hill climbing (random swap, accept only better tours)
3. Simulated annealing (2-opt neighbour, Metropolis acceptance)
4. Gradient descent (continuous relaxation with softmax + penalty)
5. Greedy algorithm (nearest neighbour)

Requires numpy; matplotlib is optional (used for the figure).
Run:  python tsp_five_methods.py
"""
import math
import os
import random
import time

import numpy as np

# ------------------------------------------------------------
# Test data: fixed seed, every method sees the same 20 cities
# ------------------------------------------------------------
N_CITIES = 20
SEED = 42


def make_cities(n=N_CITIES, seed=SEED):
    rng = random.Random(seed)
    return [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]


CITIES = make_cities()
DIST = np.array([[math.dist(a, b) for b in CITIES] for a in CITIES])


def tour_length(tour):
    return sum(DIST[tour[i], tour[(i + 1) % len(tour)]] for i in range(len(tour)))


# ------------------------------------------------------------
# 5. Greedy (nearest neighbour)
# ------------------------------------------------------------
def greedy(start=0):
    unvisited = set(range(N_CITIES)) - {start}
    tour = [start]
    while unvisited:
        nxt = min(unvisited, key=lambda c: DIST[tour[-1], c])
        tour.append(nxt)
        unvisited.remove(nxt)
    return tour


# ------------------------------------------------------------
# 1. Improvement method: repeated best-improvement 2-opt from greedy
# ------------------------------------------------------------
def two_opt_improve(init=None):
    tour = list(init) if init else greedy()
    n = len(tour)
    while True:
        best_delta, best_ij = -1e-9, None
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue  # same edge pair, reversal is a no-op
                a, b = tour[i], tour[i + 1]
                c, d = tour[j], tour[(j + 1) % n]
                delta = DIST[a, c] + DIST[b, d] - DIST[a, b] - DIST[c, d]
                if delta < best_delta:
                    best_delta, best_ij = delta, (i, j)
        if best_ij is None:
            return tour
        i, j = best_ij
        tour[i + 1:j + 1] = reversed(tour[i + 1:j + 1])


# ------------------------------------------------------------
# 2. Hill climbing: random start, random swap, keep only improvements
# ------------------------------------------------------------
def hill_climbing(iters=20000, seed=1):
    r = random.Random(seed)
    tour = list(range(N_CITIES))
    r.shuffle(tour)
    cur = tour_length(tour)
    for _ in range(iters):
        i, j = r.sample(range(N_CITIES), 2)
        tour[i], tour[j] = tour[j], tour[i]
        new = tour_length(tour)
        if new < cur:
            cur = new
        else:
            tour[i], tour[j] = tour[j], tour[i]  # undo
    return tour


# ------------------------------------------------------------
# 3. Simulated annealing: accept worse tours with probability exp(-d/T)
# ------------------------------------------------------------
def simulated_annealing(T0=100.0, T_end=1e-3, alpha=0.995, per_temp=100, seed=1):
    r = random.Random(seed)
    tour = list(range(N_CITIES))
    r.shuffle(tour)
    cur = tour_length(tour)
    best, best_len = tour[:], cur
    T = T0
    while T > T_end:
        for _ in range(per_temp):
            i, j = sorted(r.sample(range(N_CITIES), 2))
            cand = tour[:i] + tour[i:j + 1][::-1] + tour[j + 1:]  # 2-opt move
            new = tour_length(cand)
            d = new - cur
            if d < 0 or r.random() < math.exp(-d / T):
                tour, cur = cand, new
                if cur < best_len:
                    best, best_len = tour[:], cur
        T *= alpha
    return best


# ------------------------------------------------------------
# 4. Gradient descent on a continuous relaxation
#    P[k, i] = "probability that step k visits city i" = row-softmax(W)
#    loss = sum_k P[k]^T D P[k+1]  (expected length, cyclic)
#           + lam * sum_i (sum_k P[k, i] - 1)^2  (each city visited once)
#    After optimisation P is decoded into a valid permutation.
# ------------------------------------------------------------
def gradient_descent(steps=3000, lr=0.5, lam=30.0, seed=1):
    n = N_CITIES
    r = np.random.default_rng(seed)
    W = r.normal(0, 0.1, (n, n))
    Dn = DIST / DIST.mean()  # normalise so the gradient scale is stable

    def softmax(x):
        e = np.exp(x - x.max(axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)

    for t in range(steps):
        P = softmax(W)
        # dL/dP[k] = D P[k+1] + D P[k-1]  (D is symmetric)
        gP = np.roll(P, -1, axis=0) @ Dn + np.roll(P, 1, axis=0) @ Dn
        gP += 2 * lam * (P.sum(axis=0) - 1.0)[None, :]  # penalty gradient
        gW = P * (gP - (gP * P).sum(axis=1, keepdims=True))  # through softmax
        W -= lr * (1 - 0.9 * t / steps) * gW  # linearly decaying step size

    P = softmax(W)
    tour = [-1] * n
    for _ in range(n):  # decode: repeatedly take the largest remaining P[k, i]
        k, i = np.unravel_index(np.argmax(P), P.shape)
        tour[k] = int(i)
        P[k, :] = -1
        P[:, i] = -1
    return tour


# ------------------------------------------------------------
# Run, compare, plot
# ------------------------------------------------------------
METHODS = [
    ("1. Improvement (2-opt)", two_opt_improve),
    ("2. Hill climbing", hill_climbing),
    ("3. Simulated annealing", simulated_annealing),
    ("4. Gradient descent", gradient_descent),
    ("5. Greedy (nearest nbr)", greedy),
]


def plot_all(results, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    best = min(r[2] for r in results)
    fig, axes = plt.subplots(1, 5, figsize=(22, 4.6))
    for ax, (name, tour, L, _) in zip(axes, results):
        loop = tour + [tour[0]]
        ax.plot([CITIES[c][0] for c in loop], [CITIES[c][1] for c in loop],
                "-", color="tab:blue", lw=1.4, zorder=1)
        ax.scatter(*zip(*CITIES), color="tab:red", s=22, zorder=2)
        for c, (x, y) in enumerate(CITIES):
            ax.annotate(str(c), (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7)
        ax.scatter(*CITIES[tour[0]], s=140, facecolors="none", edgecolors="green", lw=2, zorder=3)
        ax.set_title(f"{name}\nL = {L:.2f}" + ("  (best)" if abs(L - best) < 1e-9 else ""), fontsize=10)
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    print(f"Figure saved to {path}")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    results = []
    print(f"Number of cities: {N_CITIES}  (seed {SEED})\n")
    for name, fn in METHODS:
        t0 = time.perf_counter()
        tour = fn()
        sec = time.perf_counter() - t0
        assert sorted(tour) == list(range(N_CITIES)), f"{name} produced an invalid tour"
        L = float(tour_length(tour))
        results.append((name, tour, L, sec))
        print(f"{name:<26} length={L:8.2f}  time={sec:7.3f}s")
        print(f"   tour: {tour}")
    plot_all(results, os.path.join(here, "tsp_results.png"))
