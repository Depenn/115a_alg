# SAT Solver via Truth-Table Enumeration (sat.py)

A Python program that solves the
[Boolean satisfiability problem (SAT)](https://en.wikipedia.org/wiki/Boolean_satisfiability_problem)
by **systematically enumerating every row of the truth table**.

## How It Works

1. **Tokenize & Parse** — a Boolean expression given as a string (e.g.
   `"(x1 or x2) and (~x1 or ~x2)"`) is converted into an expression tree (AST).
   Supported operators: `and` (`&`), `or` (`|`), `not` (`~`), and parentheses.
   Precedence: `not` > `and` > `or`.
2. **Extract variables** — unique variables are collected and sorted (natural
   sort, so `x10` comes after `x9`).
3. **Systematic enumeration** — for `n` variables, all `2^n` assignments are
   generated with a binary counter: bit `k` of integer `i`
   (`i = 0 .. 2^n - 1`) is the value of variable `k`. This yields the rows of
   the truth table in the standard order.
4. **Evaluate** — every assignment is evaluated against the AST (True/False).
5. **Conclude** — if any row evaluates to TRUE, the formula is **SAT**
   (satisfiable) and every satisfying assignment is printed; otherwise it is
   **UNSAT**.

## Complexity

Brute force: checking all `2^n` assignments → `O(2^n)` evaluations.
This is expected because SAT is an **NP-complete** problem (Cook 1971, Levin 1973);
no polynomial algorithm for the general case is known.

## Usage

```
python sat.py "BOOLEAN_FORMULA"
```

With no argument, the program uses the built-in example
`(x1 or x2) and (~x1 or ~x2)`.

### Example output

```
> python sat.py "(x1 or x2) and (~x1 or ~x2)"

Formula : (x1 or x2) and (~x1 or ~x2)
Variables: x1, x2
Enumerated assignments (2^2 = 4 rows)

x1 | x2 | result
---+----+-------
F  | F  | F
F  | T  | T
T  | F  | T
T  | T  | F

SAT - the formula is satisfiable.
   x1=F, x2=T
   x1=T, x2=F
```

## Test Cases

| Formula | Result |
|---|---|
| `(x1 or x2) and (~x1 or ~x2)` | SAT (x1=F,x2=T and x1=T,x2=F) |
| `(x1 or x2) and (~x1) and (~x2)` | UNSAT |
| `(~x1 or x2) and (~x2 or x3)` | SAT (4 assignments) |
| `(x1 & ~x2) \| (x2 & x3)` | SAT (using `&`, `\|` aliases) |
| `x1 or ~x1` | SAT (tautology, 2 assignments) |

## References

- Wikipedia: [Boolean satisfiability problem](https://en.wikipedia.org/wiki/Boolean_satisfiability_problem)