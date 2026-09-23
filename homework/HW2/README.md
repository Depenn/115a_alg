# HW2 — Recurrence Relations

Solving 4 recurrence relations: computing the closed-form (exact) expression and the **Big O** complexity.

## Problems

1. `T(n) = T(n-1) + 8`, `T(1) = 1`
2. `T(n) = 2·T(n-1) + 9`, `T(1) = 1`
3. `T(n) = 2·T(n/2) + 1`, `T(1) = 1`
4. `T(n) = T(n/2) + 1`, `T(1) = 1`

## Answers

| No | Recurrence            | Exact form        | Big O   |
|----|----------------------|-------------------|---------|
| 1  | T(n) = T(n-1) + 8    | 8n - 7            | Θ(n)    |
| 2  | T(n) = 2·T(n-1) + 9  | 10·2^(n-1) - 9    | Θ(2^n)  |
| 3  | T(n) = 2·T(n/2) + 1  | 2n - 1            | Θ(n)    |
| 4  | T(n) = T(n/2) + 1    | log₂(n) + 1       | Θ(log n)|

Full step-by-step solutions (unrolling + Master Theorem verification): see **[solutions.md](solutions.md)**.

## Automated Verification

The script **`verify_recurrences.py`** (Python 3, no dependencies) compares every exact formula
against the direct recursive computation of `T(n)` for many values of `n`. Test result: **all formulas match (`ALL MATCH`)**.

### How to run

```sh
python verify_recurrences.py
```

### Output summary

```
R1: ALL MATCH
R2: ALL MATCH
R3: ALL MATCH
R4: ALL MATCH

All exact formulas verified!
```

- **R1** verified for `n = 1..127`
- **R2** verified for `n = 1..25`
- **R3 & R4** verified for `n = 1, 2, 4, ..., 128` (powers of two)

> Note: R3 & R4 are defined for `n` a power of two (recurrence `n/2`), and their exact forms
> are valid for `n = 2^k`.

## Folder Structure

```
HW2/
├── README.md               ← this summary
├── solutions.md            ← step-by-step solutions
└── verify_recurrences.py   ← automated verification script
```