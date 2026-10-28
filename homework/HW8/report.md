# HW8 — Traveling Salesman Problem with Five Methods

**Task:** solve the Traveling Salesman Problem (TSP) with five methods — improvement method,
hill climbing, simulated annealing, gradient descent and greedy — on the **same test data**.

Code is in `code/`:

* `tsp_five_methods.py` — the five solvers, comparison table and the 5-panel figure
* `benchmark.py` — repeats the randomized methods over 30 seeds
* `tsp_results.png` — figure produced by the first script

Run: `python code/tsp_five_methods.py` (needs `numpy`, `matplotlib` optional).

---

## 0. EasySummary

* **TSP:** visit every city exactly once and return to the start with the shortest total distance.
  With 20 cities there are about 6 × 10^16 tours, so brute force is impossible.
* **Same data for all:** 20 cities, random coordinates in [0,100]², `random.Random(42)`.
* **Best length found: 352.32.** Three methods reach it (2-opt, simulated annealing, and
  gradient descent with a lucky seed). Greedy gives 460.51; hill climbing gets stuck.
* **Fast and good here:** 2-opt starting from the greedy tour reached 352.32 in under 1 ms.
* **Most reliable among random methods:** simulated annealing hit 352.32 for all 30 seeds.

---

## 1. Problem Definition

For a tour `π = (π0, …, π(n-1))`:

```
L(π) = Σ_{k=0}^{n-1} d(π_k, π_{(k+1) mod n})
```

```python
def tour_length(tour):
    return sum(DIST[tour[i], tour[(i + 1) % len(tour)]] for i in range(len(tour)))
```

## 2. Test Data

```python
N_CITIES = 20
rng = random.Random(42)
CITIES = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(N_CITIES)]
DIST = np.array([[math.dist(a, b) for b in CITIES] for a in CITIES])
```

The seed is fixed, so every method faces the identical problem.

## 3. The Five Methods

### 3.1 Improvement method (2-opt)
Start from the greedy tour. Look at every pair of edges `(a,b)` and `(c,d)`; replacing them with
`(a,c)` and `(b,d)` (reversing the segment between) changes the length by

```
Δ = d(a,c) + d(b,d) − d(a,b) − d(c,d)
```

Each round takes the move with the most negative Δ and repeats until no move improves the tour.
Deterministic, O(n²) per round. Ends in a local optimum (no 2-opt move can improve it).

### 3.2 Hill climbing
Random starting tour; repeatedly swap two random cities and **keep the swap only if the tour
gets shorter** (20,000 iterations). Never accepts a worse tour, so it gets trapped in local optima.

### 3.3 Simulated annealing
Random start, 2-opt neighbour (reverse a random segment). A worse tour (Δ > 0) is accepted with
probability `exp(−Δ/T)`. Temperature starts at `T0 = 100` and is multiplied by `0.995` each
level (100 moves per level) until `T < 10⁻³`. High `T` explores freely; low `T` behaves like hill
climbing. The best tour seen is returned.

### 3.4 Gradient descent
TSP is discrete, so it is **relaxed to a continuous problem**. Let `P[k,i]` be the "probability
that step `k` visits city `i`", with `P = row-softmax(W)`.

```
loss = Σ_k P[k]ᵀ D P[k+1]  +  λ Σ_i ( Σ_k P[k,i] − 1 )²
        (expected length)       (each city visited once)
```

The gradient is derived by hand (including the backward pass through softmax) and `W` is updated
for 3000 steps with a linearly decaying step size (lr 0.5 → 0.05, λ = 30). Finally `P` is decoded
into a valid permutation by repeatedly taking the largest remaining `P[k,i]`. Nothing guarantees
that the penalty reaches zero or that the decoded tour is good — it is a heuristic.

### 3.5 Greedy (nearest neighbour)
Start at city 0 and always move to the closest unvisited city. O(n²), no backtracking, so the last
edges can be very long.

## 4. Results

Default seed (`seed=1` for the randomized methods), single run:

| Method | Tour length | Time |
|---|---|---|
| 1. Improvement (2-opt) | **352.32** | ~0.001 s |
| 2. Hill climbing | 497.19 | ~0.10 s |
| 3. Simulated annealing | **352.32** | ~1.3 s |
| 4. Gradient descent | 552.67 | ~0.10 s |
| 5. Greedy | 460.51 | ~0 s |

![results](code/tsp_results.png)

Because three methods are random, one run says little. `benchmark.py` repeats them over seeds 1–30
(2-opt and greedy are deterministic):

| Method | Best | Mean | Worst | Time/run |
|---|---|---|---|---|
| Improvement (2-opt) | 352.32 | 352.32 | 352.32 | ~0 s |
| Hill climbing | 352.32 | 442.30 | 514.12 | 0.10 s |
| Simulated annealing | 352.32 | 352.32 | 352.32 | 2.1 s |
| Gradient descent | 352.32 | 402.58 | 757.74 | 0.24 s |
| Greedy | 460.51 | 460.51 | 460.51 | ~0 s |

## 5. Analysis

* **Gradient descent is the most seed-dependent:** 352.32 for the best seed, 757.74 for the worst,
  and 552.67 for the default seed in the single run. The single-run table above should therefore
  not be read as "gradient descent is worse than greedy" — on average (402.58) it is better.
* **Simulated annealing** was the most reliable randomized method (352.32 for all 30 seeds) but
  cost ~2 s, thousands of times more than 2-opt.
* **2-opt after greedy** found 352.32 instantly on this data. It has no randomness to rescue it
  from a local optimum, so on other datasets it may stop above the best tour; this dataset just
  happened to be kind to it.
* **Hill climbing** (swap moves, accept only improvements) has the worst average among the search
  methods, and its tour shows long crossing edges — a symptom of a local optimum.
* **Greedy** is instant but 30% longer than the best here.
* 352.32 is the best length *found*; I did not prove it optimal (that would need an exact method
  such as Held–Karp, O(n²·2ⁿ)). All five tours were checked to be valid permutations.

| Method | Time complexity | Escapes local optima? |
|---|---|---|
| Greedy | O(n²) | No (constructive) |
| 2-opt | O(n²) per round × rounds | No |
| Hill climbing | O(iters · n) | No |
| Simulated annealing | O(iters · n) | Yes, via worse moves |
| Gradient descent | O(steps · n³) | Not guaranteed |

## 6. Limitations

* One 20-city dataset; results on other datasets or sizes may differ.
* Parameters (iterations, `T0`, `α`, `λ`, learning rate) were not tuned; the gradient-descent
  result in particular depends heavily on them.
* Timings are from one machine and include Python overhead.
