# Plan: SAT Solver using Systematic Truth-Table Enumeration

**Goal:** Write a Python program that takes a Boolean formula string and determines satisfiability/unsatisfiability by opening all possible assignments (2^n) in a truth table — a brute-force O(2^n) approach, as required by the assignment.

## 1. Understand the concepts

Based on the saved Wikipedia material (`Boolean satisfiability problem - Wikipedia.html`):

- *Literal*: a variable (positive literal) or its negation (negative literal).
- *Clause*: a disjunction (OR) of one or more literals.
- *CNF* (Conjunctive Normal Form): a conjunction (AND) of clauses.
- *Satisfiable*: there exists an assignment of True/False to the variables that makes the formula TRUE.
- SAT was the first problem proven NP-complete (Cook 1971 / Levin 1973); no polynomial algorithm is known, so the naive approach of enumerating all 2^n assignments (opening the truth table) is the basic method requested here.

## 2. Files to create (in `homework/HW3/`)

- `sat.py` — main program (parser + evaluator + table enumeration + result output)
- `README.md` — short report (explanation, example output, Wikipedia references) *[optional]*

## 3. Design of `sat.py`

| Step | Function | Description |
|---|---|---|
| a | `tokenize` / parser | Convert a string like `"(x1 or ~x2) and (x2 or x3)"` into an AST (expression tree). Recognizes `and`, `or`, `not` (aliases `&`, `|`, `~`), parentheses, variables `xN`. |
| b | `get_variables` | Collect and sort unique variables (x1, x2, ...). |
| c | `evaluate` | Evaluate the AST against one assignment → True/False. |
| d | `enumerate_assignments` | Systematic enumeration: loop `i` from `0` to `2^n-1`; bit `k` of `i` is the value of variable `k` (binary counter) — yields every truth-table row in order. |
| e | `print_truth_table` | Print the table: variable columns + formula result, one row per assignment. |
| f | `main` | Parse, enumerate, collect all satisfying assignments, then conclude **SAT** (show assignments) or **UNSAT**. |

## 4. Implementation

- Recursive-descent parser with precedence: `not` > `and` > `or`, respecting parentheses.
- Evaluate directly on the expression tree.
- Enumerate all 2^n rows following the assignment's "systematically write the truth table" spirit.

## 5. Testing (test cases)

- `(x1 or x2) and (~x1 or ~x2)` → **SAT** (x1=T,x2=F and x1=F,x2=T).
- `(x1 or x2) and (~x1) and (~x2)` → **UNSAT**.
- `(~x1 or x2) and (~x2 or x3)` → **SAT**.
- Small verbose case (n=1) to confirm the table row order is correct.
- Manually verify a couple of table rows.

## 6. Validation & completion

- Run `python sat.py "<formula>"` for each test case; compare results against manual computation.
- Format code / check for errors.
- (Optional) write the README report.