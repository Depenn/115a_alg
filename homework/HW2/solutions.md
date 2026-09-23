# HW2 — Recurrence Relations

Solve each of the following recurrence relations: compute the closed form (exact) expression and the Big O complexity.

Problems:

1. `T(n) = T(n-1) + 8`, `T(1) = 1`
2. `T(n) = 2·T(n-1) + 9`, `T(1) = 1`
3. `T(n) = 2·T(n/2) + 1`, `T(1) = 1`
4. `T(n) = T(n/2) + 1`, `T(1) = 1`

---

## 1. T(n) = T(n-1) + 8, T(1) = 1

**Unrolling:**

```
T(n) = T(n-1) + 8
     = T(n-2) + 8 + 8
     = T(n-3) + 3·8
     = ...
     = T(1) + (n-1)·8
     = 1 + 8(n-1)
```

**Exact form:**

```
T(n) = 8n - 7
```

Check small values:

```
T(1) = 8(1) - 7 = 1   ✓
T(2) = 8(2) - 7 = 9   ✓ (T(1) + 8 = 9)
T(3) = 8(3) - 7 = 17  ✓ (9 + 8 = 17)
```

**Big O:** Θ(n)

---

## 2. T(n) = 2·T(n-1) + 9, T(1) = 1

**Unrolling:**

```
T(n) = 2·T(n-1) + 9
     = 2(2·T(n-2) + 9) + 9
     = 4·T(n-2) + 2·9 + 9
     = 8·T(n-3) + 4·9 + 2·9 + 9
     = ...
     = 2^k · T(n-k) + 9(2^k - 1)
```

Take `k = n-1` (down to T(1)):

```
T(n) = 2^(n-1) · T(1) + 9(2^(n-1) - 1)
     = 2^(n-1) + 9·2^(n-1) - 9
     = 10·2^(n-1) - 9
```

**Exact form:**

```
T(n) = 10·2^(n-1) - 9   =   5·2^n - 9
```

Check small values:

```
T(1) = 10·2^0 - 9 = 1          ✓
T(2) = 10·2^1 - 9 = 11         ✓ (2·1 + 9 = 11)
T(3) = 10·2^2 - 9 = 31         ✓ (2·11 + 9 = 31)
```

**Big O:** Θ(2^n)

---

## 3. T(n) = 2·T(n/2) + 1, T(1) = 1

Assume `n = 2^k` (a power of two). **Unrolling:**

```
T(n) = 2·T(n/2) + 1
     = 2(2·T(n/4) + 1) + 1
     = 4·T(n/4) + 2 + 1
     = 8·T(n/8) + 4 + 2 + 1
     = ...
     = 2^k · T(n/2^k) + (2^k - 1)
```

Take `k = log₂n` (down to T(1)):

```
T(n) = n · T(1) + (n - 1)
     = n + n - 1
```

**Exact form:**

```
T(n) = 2n - 1
```

Check small values:

```
T(1) = 2(1) - 1 = 1    ✓
T(2) = 2(2) - 1 = 3    ✓ (2·1 + 1 = 3)
T(4) = 2(4) - 1 = 7    ✓ (2·3 + 1 = 7)
```

**Master Theorem (verification):** `a = 2`, `b = 2`, `f(n) = 1 = O(n^0)`.
Since `f(n) = O(n^(log₂2 - ε)) = O(n^(1-ε))` with ε = 1, this is case **1** → `T(n) = Θ(n^log₂2) = Θ(n)`. ✓

**Big O:** Θ(n)

---

## 4. T(n) = T(n/2) + 1, T(1) = 1

Assume `n = 2^k` (a power of two). **Unrolling:**

```
T(n) = T(n/2) + 1
     = T(n/4) + 1 + 1
     = T(n/8) + 3
     = ...
     = T(n/2^k) + k
```

Take `k = log₂n` (down to T(1)):

```
T(n) = T(1) + log₂n
     = 1 + log₂n
```

**Exact form:**

```
T(n) = log₂n + 1
```

Check small values:

```
T(1) = log₂1 + 1 = 1   ✓
T(2) = log₂2 + 1 = 2   ✓ (1 + 1 = 2)
T(4) = log₂4 + 1 = 3   ✓ (2 + 1 = 3)
```

**Master Theorem (verification):** `a = 1`, `b = 2`, `f(n) = 1`.
Since `f(n) = Θ(n^log₂1) = Θ(1)` (case 2) → `T(n) = Θ(n^log₂1 · log n) = Θ(log n)`. ✓

**Big O:** Θ(log n)

---

## Summary

| No | Recurrence                      | Exact form              | Big O        |
|----|---------------------------------|-------------------------|--------------|
| 1  | T(n) = T(n-1) + 8               | 8n - 7                  | Θ(n)         |
| 2  | T(n) = 2·T(n-1) + 9             | 10·2^(n-1) - 9          | Θ(2^n)       |
| 3  | T(n) = 2·T(n/2) + 1             | 2n - 1                  | Θ(n)         |
| 4  | T(n) = T(n/2) + 1               | log₂(n) + 1             | Θ(log n)     |

All solutions are verified against direct recursive execution by `verify_recurrences.py` (see README.md).