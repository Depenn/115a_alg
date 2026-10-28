"""Run the randomized methods over many seeds on the same 20-city data."""
import statistics as st
import time

import tsp_five_methods as m

SEEDS = range(1, 31)
rows = []
for name, fn, randomized in [
    ("Improvement (2-opt)", m.two_opt_improve, False),
    ("Hill climbing", m.hill_climbing, True),
    ("Simulated annealing", m.simulated_annealing, True),
    ("Gradient descent", m.gradient_descent, True),
    ("Greedy (nearest nbr)", m.greedy, False),
]:
    t0 = time.perf_counter()
    Ls = [float(m.tour_length(fn(seed=s) if randomized else fn())) for s in (SEEDS if randomized else [0])]
    sec = (time.perf_counter() - t0) / len(Ls)
    rows.append((name, min(Ls), st.mean(Ls), max(Ls), sec))

print("| Method | Best | Mean | Worst | Time/run |")
print("|---|---|---|---|---|")
for name, lo, mean, hi, sec in rows:
    print(f"| {name} | {lo:.2f} | {mean:.2f} | {hi:.2f} | {sec:.3f} s |")
