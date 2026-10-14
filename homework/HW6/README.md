# HW6 — A Lambda-Calculus Interpreter that Shows the Whole Computation

Week 6 homework. The task: write an interpreter for the (untyped) lambda
calculus that **shows the complete reduction process** step by step, and feed it
some λ-calculus programs. Both the **named** and the **unnamed** style are
supported.

| File | What it is |
|---|---|
| [`lambda_calculus.py`](lambda_calculus.py) | The interpreter (parser, substitution, reduction, tracing, decoding, CLI). |
| [`prelude.lc`](prelude.lc) | Church encodings (booleans, numerals, arithmetic, pairs/lists, `Y`) auto-loaded at startup. |
| [`examples/`](examples) | Seven ready-to-run λ-calculus programs. |
| [`tests/test_lambda.py`](tests/test_lambda.py) | 23 self-checks that reduce real terms and read the answers back. |
| [`AI過程.md`](AI過程.md) | AI-use log: prompts, decisions, and the chat share link. |
| [`Referensi/`](Referensi) | The reference material this homework was based on. |

**Jump to:** [How to run](#how-to-run) ·
[What the interpreter does](#what-the-interpreter-does) ·
[A worked example](#a-worked-example) ·
[Named vs. unnamed](#named-vs-unnamed) ·
[Reduction strategies](#reduction-strategies) ·
[The example programs](#the-example-programs) ·
[Tests](#tests) ·
[Things to be careful about](#things-to-be-careful-about)

---

## How to run

```sh
# built-in demo (no arguments)
python lambda_calculus.py

# run a program file
python lambda_calculus.py examples/01_boolean.lc

# evaluate a term straight from the command line
python lambda_calculus.py -e "ADD TWO THREE"
python lambda_calculus.py -e "let rec fact = \n. IF (IS_ZERO n) ONE (MULT n (fact (PRED n))) in fact THREE"

# the self-checks
python -m unittest discover -s tests
```

Python 3.10+; **no third-party packages** (only the standard library).

| Option | Meaning |
|---|---|
| `--strategy {normal,cbn,cbv}` | Reduction strategy (default `normal`). |
| `--max-steps N` | Give up after `N` steps (default 3000). |
| `--expand` | Expand every name first, then reduce: a **pure, name-free** β-trace. |
| `--show-expanded` | Also print the fully expanded term before reducing. |
| `--fold` | Fold sub-terms back into names (handy with `--expand`). |
| `--no-prelude` | Do not auto-load `prelude.lc`. |
| `--ascii` | Write `\` instead of `λ`. |
| `--color` / `--no-color` | Force colour on/off. |
| `-q`, `--quiet` | Print only the final line of each term. |

---

## What the interpreter does

A term is exactly the three constructs of the lambda calculus:

```
M ::= x              a variable
    | λx. M          an abstraction   (a function)
    | M M            an application   (a call)
```

Everything else is built on those three. Concretely:

1. **Parser.** Recursive descent over `\x. M` (or `λx. M`), application,
   parentheses, and the *named* sugar:

   | Sugar | Desugars to |
   |---|---|
   | `let x = t in u` | `(λx. u) t` |
   | `let x p q = t in u` | `(λx. λp. λq. t) u` |
   | `let rec f = t in u` | `(λf. u) (Y (λf. t))` |
   | `name = t` (a program line) | a named definition |

2. **Capture-avoiding substitution.** Before substituting, the interpreter
   checks whether a binder would capture a free variable of the argument; if so
   it **renames** the binder (α-conversion) and reports the rename. For example:

   ```
   (\x. \y. x) y   →→   λy'.y    [β,α x := y   (α: y→y')]
   ```

3. **Reduction**, one redex at a time, in a strategy you choose — printing the
   whole term after every step and tagging each step with what happened:

   ```
   [δ unfold IF]     a name was replaced by its definition
   [β c := TRUE]     a β-redex was contracted, showing the substitution
   [β,α …]           … and a variable was renamed to avoid capture
   ```

4. **Answer decoding.** A normal form is inspected for a familiar Church
   encoding and annotated, e.g. `λf.λx.f (f x)   = 2`, or `…   = [2, 3, 4]`.
   (Zero and `FALSE` are the *same* term, so both readings are shown:
   `= 0 / FALSE`.)

`prelude.lc` defines the usual encodings — `TRUE`, `FALSE`, `IF`, `AND`, `OR`,
`NOT`, `XOR`, `PAIR`, `FST`, `SND`, `NIL`, `Y`, `ZERO`, `SUCC`, `ADD`, `MULT`,
`POWER`, `PRED`, `SUB`, `IS_ZERO`, `IS_LESS_EQUAL`, `IS_EQUAL`, and the numerals
`ONE`…`TEN`. A program only needs to add what it wants on top.

---

## A worked example

Here is the **complete** trace of `AND TRUE FALSE` — every step, nothing hidden:

```
     0  AND TRUE FALSE
     1  (λp.λq.p q p) TRUE FALSE   [δ unfold AND]
     2  (λq.TRUE q TRUE) FALSE   [β p := TRUE]
     3  TRUE FALSE TRUE   [β q := FALSE]
     4  (λx.λy.x) FALSE TRUE   [δ unfold TRUE]
     5  (λy.FALSE) TRUE   [β x := FALSE]
     6  FALSE   [β y := TRUE]
     7  λx.λy.y   [δ unfold FALSE]

  normal form  after 7 reduction(s):  λx.λy.y   = 0 / FALSE
```

Notice the two kinds of step: `δ unfold` replaces a name by its body exactly
when the reduction needs it (the same "展開定義" idea as the course notes), and
`β` performs the actual substitution. The interpreter is doing nothing but those
two moves.

A second one, showing `IF` staying *lazy* — the untaken branch is thrown away
without ever being evaluated:

```
     0  IF TRUE ONE TWO
     1  (λc.λx.λy.c x y) TRUE ONE TWO   [δ unfold IF]
     2  (λx.λy.TRUE x y) ONE TWO   [β c := TRUE]
     3  (λy.TRUE ONE y) TWO   [β x := ONE]
     4  TRUE ONE TWO   [β y := TWO]
     5  (λx.λy.x) ONE TWO   [δ unfold TRUE]
     6  (λy.ONE) TWO   [β x := ONE]
     7  ONE   [β y := TWO]
     8  SUCC ZERO   [δ unfold ONE]
     9  (λn.λf.λx.f (n f x)) ZERO   [δ unfold SUCC]
    10  λf.λx.f (ZERO f x)   [β n := ZERO]
    11  λf.λx.f ((λf.λx.x) f x)   [δ unfold ZERO]
    12  λf.λx.f ((λx.x) x)   [β f := f]
    13  λf.λx.f x   [β x := x]

  normal form  after 13 reduction(s):  λf.λx.f x   = 1
```

And capture-avoiding substitution in action (an α-renaming is reported):

```
     0  (λx.λy.x) y
     1  λy'.y   [β,α x := y   (α: y→y')]

  normal form  after 1 reduction(s):  λy'.y
```

The free `y` is preserved: the inner binder had to be renamed so that it would
not capture the argument `y`.

---

## Named vs. unnamed

The assignment allows either style; this interpreter does both at once.

* **Named** (default). Write `AND TRUE FALSE`, `PRED THREE`, `FACT THREE`. The
  trace keeps the names and unfolds a definition lazily with a `δ` step, which
  is far shorter and matches how the derivations are written by hand.

* **Unnamed** (`--expand`). Every name is replaced by its definition *before*
  reduction starts, so the trace contains **only** `λ`, variables, applications
  and `β`-steps — the pure, name-free lambda term. Add `--fold` to print the
  names back in for readability:

  ```
  $ python lambda_calculus.py -e "ADD TWO THREE" --expand --fold
       0  ADD TWO THREE
       …
    normal form  after 28 reduction(s):  λf.λx.f (f (f (f (f x))))   = 5
  ```

  Without `--fold` the same run shows the fully expanded term at every step.
  Running a file both ways (`examples/07_letrec.lc` is built for this) is the
  cleanest demonstration that names add **no** power — they are pure notation on
  top of the three constructs.

---

## Reduction strategies

Reduction is just "find a redex and contract it", but *which* redex you pick
changes what you get. All three are implemented; the difference is visible at a
glance on the same input.

| Strategy | What it reduces | Completeness | `ADD TWO THREE` |
|---|---|---|---|
| `normal` (default) | leftmost-outermost, **under** lambdas | finds a normal form whenever one exists | `λf.λx.f(f(f(f(f x))))` = **5** (44 steps) |
| `cbn` | call-by-name; drives only the head, never under a lambda | reaches a **weak head normal form** | `λf.λx.f (TWO SUCC TWO f x)` (10 steps) |
| `cbv` | call-by-value; evaluates the operator, then the operand (values are abstractions), then contracts | weak; may diverge where `normal` doesn't | `λf.λx.f ((λf…((λf.λx.x) f x)) f x)` (32 steps) |

`cbn` and `cbv` stop as soon as the term is a "value", so their answer is an
abstraction whose body is still full of redexes — that is correct for those
strategies, and exactly the point: only **normal** order is guaranteed to hand
back a genuine normal form. Because `normal` is outermost-first and `IF` is just
the selector `λc.λa.λb. c a b`, the branch that is not chosen is discarded and
*never evaluated* — no special thunks needed.

---

## The example programs

`examples/` is a short tour, in runnable order. Each file is a program: lines
`name = term` define, lines `run term` get evaluated and traced.

| File | Shows |
|---|---|
| [`01_boolean.lc`](examples/01_boolean.lc) | Church booleans as selectors; `NOT`, `AND`, `OR`, `XOR`; `IF`. |
| [`02_numerals.lc`](examples/02_numerals.lc) | Church numerals; `SUCC`, `ADD`, `MULT`, `POWER`, and Kleene's `PRED`/`SUB`. |
| [`03_predicate.lc`](examples/03_predicate.lc) | `IS_ZERO`, `IS_LESS_EQUAL`, `IS_EQUAL`. |
| [`04_ycombinator.lc`](examples/04_ycombinator.lc) | `FACT` via `Y`, and the same thing via `let rec`. |
| [`05_fibonacci.lc`](examples/05_fibonacci.lc) | `FIB` via `Y` — recursion without a name. |
| [`06_lists.lc`](examples/06_lists.lc) | Lists as pairs; `FST`, `SND`, `RANGE`, `MAP`. |
| [`07_letrec.lc`](examples/07_letrec.lc) | The named layer: `let`, multi-parameter `let`, `let rec`. |

A taste of `examples/06_lists.lc`:

```
  normal form  after 601 reduction(s):  λf.f (λf.λx.f (f x)) (λf.f (λf.λx.f (f (f x))) (λf.f (λf.λx.f (f (f (f x)))) (λf.λx.λy.x)))   = [2, 3, 4]
  normal form  after 2724 reduction(s):  …   = [4, 9]
```

A list is a right-nested pair `(head, tail)`; the interpreter folds that
structure back into `[2, 3, 4]` for you.

---

## Tests

`tests/test_lambda.py` reduces real terms with the normal-order strategy and
then reads the answer back as a Church numeral, boolean, or list — the
arithmetic happens *inside* the interpreter, not in Python:

```
$ python -m unittest discover -s tests
.......................
Ran 23 tests in ~2s

OK
```

It checks the logic gates, `ADD MULT POWER PRED SUB`, the comparisons,
`FACT THREE = 6`, `FACT FOUR = 24`, `FIB SIX = 8`, `RANGE`/`FST`/`SND`/`MAP`,
that `let rec` equals the `Y` form, and that `(\x.\y.x) y` renames its binder and
keeps the free `y`.

---

## Things to be careful about

1. **Full traces are *long*.** That is the assignment — every step is shown — so
   `FACT FOUR` prints 6734 lines and `FIB SIX` about 4440. Use `-q` for just the
   answer, `--max-steps` to stop early, or the small inputs in `examples/`. The
   default budget (3000 steps) is enough for every bundled example.
2. **Non-terminating terms exist, and they really don't terminate.** `Y`, or
   `(λx.x x)(λx.x x)`, makes the interpreter run out of steps (and the term can
   grow without bound). It stops at `--max-steps` / `--max-size` and says so
   rather than hanging or overflowing the stack.
3. **`0` and `FALSE` are literally the same term** (`λf.λx.x` = `λx.λy.y` up to
   renaming), so the decoder prints both readings: `= 0 / FALSE`. This is a
   feature of the encoding, not a bug in the interpreter.
4. **`cbn`/`cbv` do not give normal forms.** They stop at the first "value", so
   their output still contains redexes. If you want the decoded number, use the
   default `normal` strategy.
5. **Variable names change.** Capture-avoiding substitution renames binders
   (`x → x'`, …); two terms that are α-equivalent can look different in a trace.
   The decoder ignores names, so the *answer* is unaffected.
6. **`--fold` compares *fully-expanded* definitions.** The keys are finite even
   for `Y` (expanding a definition never applies it), so folding always
   terminates; it simply rewrites a sub-term whenever that sub-term is literally
   a definition.

---

## Files

```
HW6/
├── lambda_calculus.py     ← the interpreter (parse → substitute → reduce → trace)
├── prelude.lc             ← Church encodings, auto-loaded
├── examples/
│   ├── 01_boolean.lc
│   ├── 02_numerals.lc
│   ├── 03_predicate.lc
│   ├── 04_ycombinator.lc
│   ├── 05_fibonacci.lc
│   ├── 06_lists.lc
│   └── 07_letrec.lc
├── tests/
│   └── test_lambda.py     ← 23 self-checks
├── Referensi/             ← reference material
├── AI過程.md              ← AI-use log + chat share link
└── README.md              ← this file
```

---

## Note on AI assistance

Parts of this homework were written with the help of an AI assistant. The full
record — the prompts, the decisions, and what was kept or rewritten — is in
[`AI過程.md`](AI過程.md), together with a link to the shared conversation.
Independent verification is the test suite above: `python -m unittest discover
-s tests` exercises the interpreter end to end and can be run by anyone.
