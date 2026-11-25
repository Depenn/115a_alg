"""Tests for HW12. Run:  python test_computation.py   (or  pytest)

Every machine and grammar is compared with a plain Python predicate on ALL words up to a length.
"""
import random
import re

import fsm
import grammar as gr
import pda
import turing as tm
from pda import all_words


# --------------------------------------------------------------------------- finite automata

def test_dfa_examples():
    words = all_words("ab", 10)
    assert all(fsm.dfa_a_star().accepts(w) == (set(w) <= {"a"}) for w in words)
    assert all(fsm.dfa_a_star_b_plus().accepts(w) == bool(re.fullmatch("a*b+", w)) for w in words)
    bits = all_words("01", 10)
    assert all(fsm.dfa_even_zeros().accepts(w) == (w.count("0") % 2 == 0) for w in bits)
    for m in range(1, 10):
        d = fsm.dfa_div_by(m)
        assert all(d.accepts(bin(n)[2:]) == (n % m == 0) for n in range(2000))


def test_nfa_and_subset_construction():
    for pattern in ("a", "ab", "aba", "bbab"):
        n = fsm.nfa_contains(pattern)
        d = n.to_dfa()
        for w in all_words("ab", 9):
            assert n.accepts(w) == (pattern in w) == d.accepts(w)
    for k in range(1, 8):
        n = fsm.nfa_kth_from_end_is_1(k)
        d = n.to_dfa()
        for w in all_words("01", 10):
            assert n.accepts(w) == (len(w) >= k and w[-k] == "1") == d.accepts(w)
        assert len(d) == len(d.minimize()) == 2 ** k


def test_minimize():
    small = fsm.dfa_a_count_mod4_even().minimize()
    assert len(small) == 2
    expected = {2: 2, 3: 3, 4: 3, 5: 5, 6: 4, 8: 4, 12: 5}
    for m, size in expected.items():
        d = fsm.dfa_div_by(m)
        mini = d.minimize()
        assert len(mini) == size
        assert all(mini.accepts(w) == d.accepts(w) for w in all_words("01", 9))
    # minimizing twice changes nothing
    again = fsm.dfa_div_by(6).minimize().minimize()
    assert len(again) == 4


def test_anbn_counterexample_for_random_dfas():
    rng = random.Random(7)
    for k in range(0, 10):
        d = fsm.dfa_anbn_upto(k)
        w, i, j = fsm.anbn_counterexample(d)
        assert d.accepts(w) != fsm.is_anbn(w) and i < j
    for _ in range(300):
        n = rng.randint(1, 8)
        delta = {(q, c): rng.randrange(n) for q in range(n) for c in "ab"}
        finals = {q for q in range(n) if rng.random() < 0.5}
        d = fsm.DFA(set(range(n)), "ab", delta, 0, finals)
        w, i, j = fsm.anbn_counterexample(d)
        assert d.accepts(w) != fsm.is_anbn(w)


# --------------------------------------------------------------------------- pushdown automata

def test_pdas():
    cases = [
        (pda.pda_anbn(), pda.is_anbn, "ab"),
        (pda.pda_balanced(), pda.is_balanced, "()"),
        (pda.pda_even_palindrome(), pda.is_even_palindrome, "ab"),
        (pda.pda_more_a_than_b(), pda.is_more_a, "ab"),
    ]
    for m, truth, alphabet in cases:
        for w in all_words(alphabet, 10):
            assert m.accepts(w) == truth(w), w


def test_pda_trace():
    path = pda.pda_even_palindrome().run_trace("abba")
    assert path[0] == ("push", 0, "$") and path[-1] == ("acc", 4, "$")
    assert pda.pda_even_palindrome().run_trace("abab") is None


# --------------------------------------------------------------------------- grammars

def test_chomsky_types():
    assert gr.G_ASTAR_BPLUS.chomsky_type() == 3
    assert gr.G_ANBN.chomsky_type() == 2
    assert gr.G_BALANCED.chomsky_type() == 2
    assert gr.G_EXPR.chomsky_type() == 2
    assert gr.G_ENGLISH.chomsky_type() == 2
    assert gr.G_ANBNCN.chomsky_type() == 1
    assert gr.G_COPY.chomsky_type() == 0


def test_grammar_languages():
    def upto(alphabet, n, pred):
        return {w for w in all_words(alphabet, n) if pred(w)}

    assert gr.G_ASTAR_BPLUS.language(10) == upto("ab", 10, lambda w: re.fullmatch("a*b+", w))
    assert gr.G_ANBN.language(12) == upto("ab", 12, lambda w: w and pda.is_anbn(w))
    assert gr.G_BALANCED.language(10) == upto("()", 10, pda.is_balanced)
    assert gr.G_ANBNCN.language(12) == upto("abc", 12, lambda w: w and gr.is_anbncn(w))
    assert gr.G_COPY.language(6) == upto("ab", 6, gr.is_copy)


def test_same_language_in_every_model():
    """The grammar, the automaton and the Turing machine define the same set of words."""
    words = all_words("ab", 10)
    g = gr.G_ANBN.language(10)
    p = {w for w in words if pda.pda_anbn().accepts(w)}
    f = {w for w in words if fsm.dfa_anbn_upto(5).accepts(w)}
    assert g == p - {""}
    assert f == {w for w in g if len(w) <= 10} | {""}     # the DFA is only right up to n = 5
    t = {w for w in all_words("abc", 9) if tm.tm_anbncn().accepts(w)}
    assert t - {""} == gr.G_ANBNCN.language(9)


def test_derivations():
    path = gr.G_ANBNCN.derivation("aabbcc")
    assert path[0] == ("S",) and "".join(path[-1]) == "aabbcc" and len(path) == 5
    for a, b in zip(path, path[1:]):
        assert b in gr.G_ANBNCN.successors(a)
    assert gr.G_ANBNCN.derivation("aabbc") is None
    assert "".join(gr.G_COPY.derivation("abab")[-1]) == "abab"


def test_random_generation():
    rng = random.Random(1)
    for _ in range(50):
        w = gr.G_ANBNCN.generate(rng).replace(" ", "")
        assert gr.is_anbncn(w)
        assert pda.is_balanced(gr.G_BALANCED.generate(rng).replace(" ", ""))
        e = gr.G_EXPR.generate(rng, max_len=15)
        eval(e, {}, {"x": 3, "y": 4})            # every expression is valid Python
        words = gr.G_ENGLISH.generate(rng).split()
        assert words[0] in ("the", "a") and 3 <= len(words) <= 7


def test_cyk():
    for w in all_words("ab", 10)[1:]:
        assert gr.cyk(gr.CNF_ANBN, w)[0] == pda.is_anbn(w)
    for w in all_words("()", 10)[1:]:
        assert gr.cyk(gr.CNF_BALANCED, w)[0] == pda.is_balanced(w)


# --------------------------------------------------------------------------- Turing machines

def test_tm_deciders():
    m = tm.tm_anbncn()
    for w in all_words("abc", 7):
        assert m.accepts(w) == tm.is_anbncn(w), w
    p = tm.tm_palindrome()
    for w in all_words("ab", 10):
        assert p.accepts(w) == (w == w[::-1]), w


def test_tm_functions():
    inc = tm.tm_binary_increment()
    for n in range(300):
        assert int(inc.output(bin(n)[2:]), 2) == n + 1
    add = tm.tm_unary_add()
    for a in range(8):
        for b in range(8):
            assert add.output("1" * a + "+" + "1" * b) == "1" * (a + b)


def test_busy_beavers_and_timeout():
    expected = {2: (6, 4), 3: (14, 6), 4: (107, 13)}
    for n, (steps, ones) in expected.items():
        r = tm.busy_beaver(n).run("")
        assert r.status == "accept" and r.steps == steps and r.tape.count("1") == ones
    assert tm.tm_walk_right_forever().run("", max_steps=500).status == "timeout"
    for budget in (5, 50, 500):
        assert not tm.halts_within(tm.tm_skip_ones(), "1" * (budget + 1), budget)
        assert tm.halts_within(tm.tm_skip_ones(), "1" * budget, budget)


def test_anbncn_steps_quadratic():
    m = tm.tm_anbncn()
    ratios = [m.run("a" * n + "b" * n + "c" * n).steps / n ** 2 for n in (8, 16, 32, 64)]
    assert all(4 <= r <= 5 for r in ratios)


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"all {len(tests)} tests passed")
