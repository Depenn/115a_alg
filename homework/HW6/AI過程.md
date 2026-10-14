# AI 過程 — How This Homework Was Made (with AI)

> **Shared conversation link:**
> `<PASTE THE SHARE URL HERE>`
>
> (Replace the line above with the public share link of the chat used for this
> homework, e.g. a ChatGPT/Gemini/Claude share URL. Until it is pasted, this
> document is the process record required by the assignment.)

---

## 1. The task

Write a lambda-calculus interpreter that shows the **complete computation
process** (every reduction step), take some λ-calculus programs as input, and
allow either the **named** or the **unnamed** style. Work that used AI must
share a URL or a process document, and the reference material is in
`Referensi/`.

## 2. What was used

| Item | Value |
|---|---|
| Assistant | OpenCode coding agent — model **Big Pickle** (`opencode/big-pickle`) |
| Language / runtime | Python 3.10+ (standard library only) |
| Sources consulted | everything under `Referensi/`, especially `04c-LambdaCalculus/` (the encodings and the `Y` combinator) and the course note `算法：LambdaCalculus.md` (the β-reduction / `IF` derivation style) |

## 3. The prompts (log)

The work was driven by a short sequence of prompts. Each row is one prompt and
what came out of it.

| # | Prompt (paraphrased) | Result |
|---|---|---|
| 1 | *"Help me with this assignment"* + the assignment text. | Read all of `Referensi/` and the earlier `HW4`/`HW5` READMEs to learn the expected format; proposed a plan. |
| 2 | Answered follow-ups: implement in **Python**, docs in **English**, support **both** named and unnamed, keep the **full** scope. | Final plan fixed; agreed to build the interpreter + examples + tests + README + this document. |
| 3 | *"Continue"* / build it. | `lambda_calculus.py`, `prelude.lc`, the seven `examples/*.lc`, and `tests/test_lambda.py` were written; all 23 tests made to pass. |
| 4 | *"Continue"* (documentation). | `README.md` and this file. |

The assistant did **not** need to be told the encodings: they were taken from
`Referensi/04c-LambdaCalculus/` so they match the course — for example
`AND = λp.λq. p q p`, `MULT = λm.λn.λf. m (n f)`, Kleene's
`PRED = λn.λf.λx. n (λg.λh. h (g f)) (λu.x) (λu.u)`, and
`Y = λf. (λx. f (x x)) (λx. f (x x))`.

## 4. Key decisions (and why)

1. **Terms are three frozen dataclasses** (`Var`, `Abs`, `App`). Being hashable
   lets the program compare whole terms by structure — used by the decoder and
   by the `--fold` feature.
2. **`δ`-steps for names.** The reference derivations show a definition being
   *unfolded when it is needed* ("展開 IF 定義"), so the named layer is modelled
   as a `δ`-step rather than by expanding everything up front. `--expand` gives
   the opposite, pure β-only view, so both readings in the assignment are
   available from the same interpreter.
3. **Three strategies**, because "which redex" changes the answer:
   normal order (complete), call-by-name and call-by-value (weak). A table in
   the README compares them on one input.
4. **One step per line, with a tag** `[β …]`, `[δ …]`, `[β,α …]`. This is the
   "show the complete process" requirement, and the tags make the two reduction
   rules visible instead of hidden.
5. **Decode the answer, don't just print it.** Church numerals, booleans and
   lists are recognised in the normal form so the output reads `… = 5` or
   `… = [2, 3, 4]`.
6. **Guard against non-termination.** `Y` diverges, so a step budget
   (`--max-steps`) and a size budget (`--max-size`) stop runaway terms; the
   `--fold` map deliberately skips definitions with no normal form.

## 5. What the AI produced vs. what was checked

* AI produced: the parser, substitution, the three strategies, the tracer, the
  decoder, `prelude.lc`, the example programs, the tests, and these docs.
* Human review / verification: running every example end to end, running the
  test suite, and checking the traces against the derivations in `Referensi/`.
  The test suite is the durable check — it reduces real terms and reads the
  answers back, so a wrong encoding would fail loudly.

## 6. How to reproduce / verify

```sh
python -m unittest discover -s tests      # 23 checks, must print OK
python lambda_calculus.py examples/01_boolean.lc
python lambda_calculus.py -e "ADD TWO THREE" --expand --fold
```

## 7. Honesty note

The encodings and the course's expected derivation style come from
`Referensi/`. The interpreter code was written with the AI assistant. Any share
link requested by the assignment should be pasted at the top of this file.
