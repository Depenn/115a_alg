# HW12 — Theory of Computation (計算理論): Automata, Grammars and Turing Machines

References: course folder [04-理論/01-計算理論](https://github.com/ccc115a/alg/tree/main/04-%E7%90%86%E8%AB%96/01-%E8%A8%88%E7%AE%97%E7%90%86%E8%AB%96)
and the book [數學、語言、機器與程式](https://github.com/ccc115a/alg/tree/main/04-%E7%90%86%E8%AB%96/01-%E8%A8%88%E7%AE%97%E7%90%86%E8%AB%96/_book).
All code here is written from scratch. The course folder was only used for the list of topics and the example
languages (aⁿ, even 0s, aⁿbⁿ, aⁿbⁿcⁿ). Lambda calculus was already covered in HW6, so it is not repeated here.

| # | File | Model (Chomsky type) | What it implements |
|---|---|---|---|
| 1 | `fsm.py` | finite automata (type 3) | DFA, NFA with ε-moves, subset construction, Moore minimization, pigeonhole proof that aⁿbⁿ is not regular |
| 2 | `pda.py` | pushdown automata (type 2) | nondeterministic PDA searched with BFS: aⁿbⁿ, balanced brackets, w wᴿ, #a > #b |
| 3 | `grammar.py` | grammars (types 0–3) | rule parser, automatic Chomsky type, random generation, language enumeration, shortest derivation, CYK parsing |
| 4 | `turing.py` | Turing machines (type 0) | simulator with an infinite tape, deciders, machines that compute functions, busy beavers, halting demo |

* `python fsm.py`, `python pda.py`, `python grammar.py`, `python turing.py` run the demos (all output is in `results.txt`).
* `python test_computation.py` (or `pytest`) runs the tests → `all 16 tests passed`.
* Pure Python 3, no extra packages.

---

## 0. Summary

* **The Chomsky hierarchy** is a ladder of machines and grammars. Each step up can recognise more languages:

  | Type | Grammar rules | Machine | Example here | Not possible one level lower |
  |---|---|---|---|---|
  | 3 regular | A → a B, A → a, A → ε | finite automaton (no memory beyond the state) | a\*b+, even number of 0s, binary divisible by 3 | — |
  | 2 context-free | A → anything | pushdown automaton (one stack) | aⁿbⁿ, balanced ( ), w wᴿ | aⁿbⁿ (needs to count without bound) |
  | 1 context-sensitive | \|left\| ≤ \|right\| | linear bounded automaton | aⁿbⁿcⁿ | aⁿbⁿcⁿ (one stack can match only two counts) |
  | 0 unrestricted | any rule | Turing machine | any computable function; the "halts" set of §4.5 | the halting set (recognisable, but not decidable) |

  `chomsky_type()` classifies a *grammar*, not a *language*. `G_COPY` (w w) uses ε-rules, so the grammar is
  type 0, but the language {w w} is context-sensitive: it also has a type-1 grammar, not built here.

* **Every machine is checked against plain Python** on *all* words up to a length (for example all 2047 words of length ≤ 10 over {a, b}), not just a few examples.
* **NFA vs DFA:** "the k-th symbol from the end is 1" needs only k+1 NFA states, but its minimal DFA has exactly **2ᵏ** states (1024 for k = 10).
* **aⁿbⁿ is not regular:** for any DFA, `anbn_counterexample` finds a concrete word it gets wrong (pigeonhole argument). It was tested on 300 random DFAs.
* **The Turing machine for aⁿbⁿcⁿ** uses about **4n² steps** (16,577 steps for n = 64).
* **Busy beavers:** 2, 3 and 4 states give 6, 14 and 107 steps and leave 4, 6 and 13 ones. These match the
  known champions: S(2), S(4) and Σ(2), Σ(3), Σ(4). The 3-state machine is the most-1s champion, not the most-steps one.
* **Halting:** a simulator with a step budget can say "halts" but never "loops forever". For every budget there is an input on which it is wrong, which is the practical side of the halting problem.

---

## 1. Finite automata (`fsm.py`)

### 1.1 DFA

A DFA is (Q, Σ, δ, q₀, F). `DFA.delta` is a dict `(state, symbol) → state`. A missing transition means
"reject", and `complete()` adds an explicit dead state. `trace()` returns the path of states:

```
even number of 0s  (2 states)
  '010'        -> True   path E O O E
  '10100'      -> False  path E E O O E O
binary divisible by 3  (3 states)
  '1001'       -> True   path 0 1 2 1 0
  '1010'       -> False  path 0 1 2 2 1
```

For "divisible by m" the state is the remainder r. Reading bit b turns the number v into 2v + b, so the
transition is r → (2r + b) mod m. The demo checks all n < 1000, and the tests check m = 1..9 for all n < 2000.

### 1.2 NFA and subset construction

An NFA may have several moves for one symbol, plus ε-moves that read nothing. `NFA.accepts` keeps the
**set** of states it could be in, closed under ε-moves. `to_dfa()` is the subset construction: each DFA
state is one of these sets, and only the reachable sets are built.

"The k-th symbol from the end is 1": the NFA guesses which 1 is k from the end (k + 1 states). A DFA has
to remember the last k symbols, so it needs 2ᵏ states:

| k | NFA states | DFA states (subset) | minimal DFA |
|---|---|---|---|
| 1 | 2 | 2 | 2 |
| 3 | 4 | 8 | 8 |
| 5 | 6 | 32 | 32 |
| 10 | 11 | 1024 | 1024 |

NFAs and DFAs recognise exactly the same languages, but the NFA can be exponentially smaller.

### 1.3 Minimization (Moore's algorithm)

Start with two blocks, final and non-final. Repeatedly split a block when its states move to different blocks
on some symbol, and stop when no block splits. Each block becomes one state of the minimal DFA.

| DFA | states | minimal |
|---|---|---|
| even number of a's, built as "count mod 4, finals {0, 2}" | 4 | 2 |
| binary divisible by 6 | 6 | 4 |
| binary divisible by 8 | 8 | 4 |
| binary divisible by 3, 5 | 3, 5 | 3, 5 |

For 6: remainders 1 and 4 behave the same (both go to 2 on a 0 and to 3 on a 1), and so do 2 and 5.
For 8: only the last three bits matter, so the minimal DFA counts trailing zeros (0, 1, 2, ≥3).

### 1.4 Why a DFA cannot recognise aⁿbⁿ

A complete DFA with N states reads a⁰, a¹, …, a^N. That is N + 1 prefixes but only N states, so two prefixes
aⁱ and aʲ (i < j) end in the same state. From then on the DFA cannot tell them apart, so aⁱbⁱ and aʲbⁱ get the
same answer, but only the first is in the language. `anbn_counterexample(dfa)` carries out this argument and
returns the word the DFA gets wrong:

```
DFA correct up to n=3 (8 states): a^4 and a^5 reach the same state -> wrong on 'aaaabbbb' (says False, truth True)
DFA correct up to n=8 (18 states): a^9 and a^10 reach the same state -> wrong on 'aaaaaaaaabbbbbbbbb' (says False, truth True)
```

Adding states only pushes the mistake further out. The tests also run it on 300 random DFAs (1–8 states), and
it finds a wrong word every time.

---

## 2. Pushdown automata (`pda.py`)

A PDA is a finite automaton plus a **stack**. A transition is
`(state, input symbol or ε, top of stack or ε) → [(new state, string to push)]`.
The machine may be nondeterministic, so `accepts()` does a **breadth-first search over configurations**
(state, input position, stack contents). It accepts if any branch reaches a final state after reading the
whole input. The stack height is limited to len(w) + 2, so the search is finite. All four machines below
never need more.

| Machine | Idea | Configurations explored (example) |
|---|---|---|
| aⁿbⁿ | push A for every a, pop one for every b | `aaabbb`: 9 |
| balanced ( ) | push on (, pop on ) | `(()())`: 9 |
| w wᴿ (even palindromes) | push the first half, pop and compare the second half; **guess** the middle with an ε-move | `baaaab`: 21 |
| #a > #b | the stack holds the surplus (A's or B's) | `bbaaa`: 7 |

Each machine agrees with its Python predicate on all 2047 words of length ≤ 10. The accepting computation
for `abba` shows the guessed middle:

```
push  read ''      stack $
push  read 'a'     stack a$
push  read 'ab'    stack ba$
pop   read 'ab'    stack ba$      <- epsilon move: "the middle is here"
pop   read 'abb'   stack a$
pop   read 'abba'  stack $
acc   read 'abba'  stack $
```

w wᴿ really needs the nondeterminism. A deterministic PDA cannot know where the middle is.

---

## 3. Grammars (`grammar.py`)

### 3.1 Representation and Chomsky type

`Grammar.parse("S -> a S b | a b")` reads rules. Tokens are separated by spaces, a token starting with an
upper-case letter is a non-terminal, and `ε` is the empty string. A left side may have several symbols
(`c B -> B c`). `chomsky_type()` returns the most restrictive type that all rules satisfy:

* **3** if every rule is A → a B, A → a or A → ε (right-linear)
* **2** if every left side is a single non-terminal
* **1** if |left| ≤ |right| for every rule (S → ε is allowed only if S is never on a right side)
* **0** otherwise

| Grammar | Rules | Type | Words found (length limit) |
|---|---|---|---|
| a\*b+ | S → a S \| b B \| b, B → b B \| b | 3 | 21 words (≤ 6) |
| aⁿbⁿ | S → a S b \| a b | 2 | ab, aabb, aaabbb, aaaabbbb |
| balanced ( ) | S → ( S ) S \| ε | 2 | 9 words (≤ 6): ε, (), (()), ()(), … |
| aⁿbⁿcⁿ | S → a b c \| a S B c, c B → B c, b B → b b | 1 | abc, aabbcc, aaabbbccc |
| w w (copy) | see `G_COPY` (uses E → ε) | 0 | 15 words (≤ 6): ε, aa, bb, aaaa, abab, … |
| expressions | E → E + T \| T, T → T * F \| F, F → ( E ) \| x \| y \| 2 | 2 | random generation |
| toy English | S → NP VP, NP → Det N \| Det Adj N, … | 2 | random generation |

**aⁿbⁿcⁿ:** each `a S B c` adds one a, one B and one c. `c B → B c` moves every B to the left past the c's,
and `b B → b b` turns it into a b only when it touches the b block. Shortest derivation of `aabbcc`:

```
S => a S B c => a a b c B c => a a b B c c => a a b b c c
```

**w w (type 0):** T writes w with a marker after every letter (`a A b B … E`). Markers move right over
terminals but never over each other, so they keep their order. A marker next to the end marker E becomes a
terminal just after E, so the copy is rebuilt from the right. `E → ε` shrinks the string, which makes the
*grammar* type 0. The *language* {w w} is still context-sensitive: a noncontracting grammar for it exists, but
it needs more rules. Shortest derivation of `abab` (8 steps):

```
S => T E => a A T E => a A b B T E => a A b B E => a b A B E => a b A E b => a b E a b => a b a b
```

### 3.2 Generating words

* `generate(rng)` picks a random applicable (rule, position) until only terminals are left. It restarts if it
  gets stuck or the form gets too long. Example output: `2 * y + 2`, `the small cat chases a student`.
  One random derivation of aⁿbⁿcⁿ (seed 0) took 8 steps to reach `aaabbbccc`.
* `language(L)` is a BFS over sentential forms, keeping only forms with at most L terminals and at most
  2L + 2 symbols, and returns every word of length ≤ L. The tests compare it with the Python predicate for
  every grammar.
* `derivation(w)` uses the same BFS to return the shortest derivation.

The cost of this BFS depends a lot on the type. aⁿbⁿcⁿ up to length 15 takes 0.03 s. The type-0 copy grammar
takes 1.4 s for length ≤ 6 and did not finish length ≤ 8 within 60 s, because markers can move in many orders.
For type 0 there is no general way around this: membership in an unrestricted grammar is only
semi-decidable, the same as halting.

### 3.3 CYK parsing

For a grammar in **Chomsky normal form** (rules A → B C or A → a), CYK decides membership with dynamic
programming. `table[i][len-1]` is the set of non-terminals that derive the substring of length `len` starting
at i. A cell is filled from every split of the substring into two shorter parts, which gives **O(n³)** time.
For aⁿbⁿ (S → A X \| A B, X → S B, A → a, B → b) and the word `aabb`:

```
len 1: A      A      B      B
len 2: -      S      -
len 3: -      X
len 4: S                 <- S derives the whole word: accepted
```

The tests check CYK for aⁿbⁿ and for balanced brackets on every non-empty word of length ≤ 10.

---

## 4. Turing machines (`turing.py`)

### 4.1 Simulator

The transition table maps `(state, read symbol) → (new state, write symbol, move L/R/S)`. The tape is a dict,
so it is unbounded in both directions. The machine **halts when no transition applies**: it accepts if it is
in an accept state, and rejects otherwise. `run()` takes `max_steps` and returns `timeout` when the limit is
reached. Machines are written as text tables:

```
q0 a -> q1 X R
q1 b -> q2 Y R
...
```

### 4.2 Decider for aⁿbⁿcⁿ

This language is not context-free, so no PDA can recognise it. The Turing machine crosses off one a (X), one
b (Y) and one c (Z) in each round. When no a's are left it checks that only Y and Z remain.

```
q0   [a]bc        q3   [X]YZ
q1   X[b]c        q0   X[Y]Z
q2   XY[c]        q4   XY[Z]
q3   X[Y]Z        q4   XYZ[_]   -> acc
```

| input | result | steps |
|---|---|---|
| `abc` | accept | 8 |
| `aabbcc` | accept | 23 |
| `aabbc` | reject | 13 |
| `abcabc` | reject | 7 |
| `acb` | reject | 1 |

Each round walks across the whole word and back, so the time is **Θ(n²)**:

| n | 1 | 4 | 16 | 64 |
|---|---|---|---|---|
| steps | 8 | 77 | 1073 | 16577 |
| steps / n² | 8.00 | 4.81 | 4.19 | 4.05 |

The palindrome machine works the same way: erase the first symbol, run to the end, compare it with the last
symbol, and come back (`abba`: 15 steps, `aabaa`: 21 steps).

### 4.3 Computing functions

* **Binary increment:** go to the last bit, then turn trailing 1s into 0s until a 0 or a blank becomes 1.
  `1011 → 1100`, `11111111 → 100000000`. Tested for all n < 300.
* **Unary addition:** `11+111 → 11111` (turn `+` into 1, erase the last 1). Tested for all a, b < 8.

### 4.4 Busy beavers

A busy beaver is an n-state, 2-symbol machine that starts on a blank tape and halts. It is a champion either
for the **most steps** before halting (S(n)) or for the **most 1s** left on the tape (Σ(n)).

| states | machine | steps until halt | 1s left |
|---|---|---|---|
| 2 | champion for both S and Σ | 6 = S(2) | 4 = Σ(2) |
| 3 | most-1s champion | 14 (not the step record) | 6 = Σ(3) |
| 4 | champion for both S and Σ | 107 = S(4) | 13 = Σ(4) |

The most-steps 3-state machine is a different one, and it is not run here. Both S(n) and Σ(n) grow faster
than any computable function of n. If it did not, we could decide halting by running every
n-state machine for that many steps.

### 4.5 Halting problem

`tm_walk_right_forever()` never halts, but after 1000 steps the simulator can only say `timeout`: "not yet",
not "never". `halts_within(machine, word, budget)` is the obvious "halting tester" (run for `budget` steps).
For each budget, the input 1^(budget+1) defeats it:

```
budget   10: input 1^11 -> tester says halts=False, truth: halts after 11 steps
budget 1000: input 1^1001 -> tester says halts=False, truth: halts after 1001 steps
```

No budget works for all machines, and Turing showed that no other method does either. Suppose `halts(p, x)`
always answered correctly, and define

```python
def paradox(p):
    if halts(p, p):     # p would halt when given its own code
        while True:     # ... so loop forever
            pass
    return              # otherwise halt
```

Then `paradox(paradox)` halts exactly when `halts(paradox, paradox)` says it doesn't. That is a
contradiction, so `halts` cannot exist. The same idea shows that membership for type-0 grammars (3.2) is
undecidable.

---

## 5. Tests

`python test_computation.py` → `all 16 tests passed` (also `pytest`: 16 passed). They check:

* **DFA/NFA:** a\*, a\*b+, even 0s against regexes or predicates on all words of length ≤ 10. "Divisible by
  m" for m = 1..9 and n < 2000. For four patterns and k = 1..7, the NFA, the subset DFA and the predicate
  agree, and the k-th-from-end DFA has exactly 2ᵏ states both before and after minimization.
* **Minimization:** sizes for m = 2, 3, 4, 5, 6, 8, 12. The language is unchanged, and minimizing twice
  changes nothing.
* **aⁿbⁿ counterexample:** correct for the "correct up to k" DFAs and for 300 random DFAs.
* **PDA:** all four machines against predicates on all words of length ≤ 10, plus the accepting trace.
* **Grammars:** Chomsky types of all 7 grammars. `language()` equals the predicate's set (a\*b+ ≤ 10,
  aⁿbⁿ ≤ 12, brackets ≤ 10, aⁿbⁿcⁿ ≤ 12, ww ≤ 6). Every derivation step is a legal rule application.
  Randomly generated words are in the language, and generated expressions are valid Python.
* **Same language in every model:** the aⁿbⁿ grammar equals the PDA, and the aⁿbⁿcⁿ grammar equals the
  Turing machine (all words over {a, b, c} of length ≤ 9).
* **CYK:** against the predicates on all non-empty words of length ≤ 10.
* **Turing machines:** aⁿbⁿcⁿ on all 3280 words over {a, b, c} of length ≤ 7, palindromes on length ≤ 10,
  increment, addition, busy-beaver steps and ones, timeout, the halting tester, and steps/n² between 4 and 5.

## 6. Limitations

* The PDA search limits the stack to len(w) + 2. That is enough for these machines, but a general PDA with
  ε-pushes could need a different bound, or a conversion to a grammar.
* `language()` limits sentential forms to 2L + 2 symbols. This is safe for the grammars here (the tests
  confirm it), but not a general proof. For type-0 grammars the search is exponential.
* CYK needs the grammar already in Chomsky normal form. The two CNF grammars were converted by hand, and
  automatic CNF conversion was not implemented.
* The Turing machines are single-tape and deterministic. Multi-tape machines (aⁿbⁿcⁿ in O(n)) and a
  universal machine that reads another machine's table from its tape were not implemented. The Python
  simulator itself plays the role of the universal machine.
