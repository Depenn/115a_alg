"""Pushdown automata (Chomsky type 2: context-free languages).

A PDA is a finite automaton plus one stack. It may be nondeterministic, so accepts() runs a
breadth-first search over configurations (state, input position, stack) and accepts if ANY
branch reaches a final state after reading the whole input.

Pure Python 3.  Run:  python pda.py
"""
from collections import deque
from itertools import product

EPS = ""


class PDA:
    def __init__(self, delta, start, finals, bottom="$"):
        # delta: (state, input symbol or EPS, stack top or EPS) -> list of (new state, push string)
        # push string is written with its first character on TOP; "" pushes nothing.
        self.delta = {k: list(v) for k, v in delta.items()}
        self.start = start
        self.finals = set(finals)
        self.bottom = bottom

    def moves(self, state, pos, stack, word):
        """All configurations reachable in one step. The stack is a string, top = stack[0]."""
        top = stack[:1]
        options = [(EPS, EPS), (EPS, top)]
        if pos < len(word):
            options += [(word[pos], EPS), (word[pos], top)]
        for c, t in options:
            for new_state, push in self.delta.get((state, c, t), ()):
                rest = stack[len(t):]
                yield new_state, pos + len(c), push + rest

    def accepts(self, word, max_stack=None, stats=None):
        """BFS over configurations. The stack is cut off at max_stack (default len(word) + 2),
        which is enough for the machines below and makes the search finite."""
        if max_stack is None:
            max_stack = len(word) + 2
        start = (self.start, 0, self.bottom)
        seen, todo = {start}, deque([start])
        while todo:
            state, pos, stack = todo.popleft()
            if pos == len(word) and state in self.finals:
                if stats is not None:
                    stats["configs"] = len(seen)
                return True
            for cfg in self.moves(state, pos, stack, word):
                if len(cfg[2]) <= max_stack and cfg not in seen:
                    seen.add(cfg)
                    todo.append(cfg)
        if stats is not None:
            stats["configs"] = len(seen)
        return False

    def run_trace(self, word):
        """One accepting path (list of configurations) found by BFS, or None."""
        max_stack = len(word) + 2
        start = (self.start, 0, self.bottom)
        parent, todo = {start: None}, deque([start])
        while todo:
            cfg = todo.popleft()
            if cfg[1] == len(word) and cfg[0] in self.finals:
                path = []
                while cfg is not None:
                    path.append(cfg)
                    cfg = parent[cfg]
                return path[::-1]
            for nxt in self.moves(*cfg, word):
                if len(nxt[2]) <= max_stack and nxt not in parent:
                    parent[nxt] = cfg
                    todo.append(nxt)
        return None


# --------------------------------------------------------------------------- examples

def pda_anbn():
    """a^n b^n, n >= 0. Push an A for every a, pop one for every b."""
    return PDA({
        ("p", "a", EPS): [("p", "A")],
        ("p", EPS, "$"): [("acc", "$")],     # empty word
        ("p", "b", "A"): [("q", "")],
        ("q", "b", "A"): [("q", "")],
        ("q", EPS, "$"): [("acc", "$")],
    }, "p", {"acc"})


def pda_balanced():
    """Balanced parentheses, e.g. (()()). Push on '(', pop on ')'. Accept when only $ is left."""
    return PDA({
        ("p", "(", EPS): [("p", "(")],
        ("p", ")", "("): [("p", "")],
        ("p", EPS, "$"): [("acc", "$")],
    }, "p", {"acc"})


def pda_even_palindrome():
    """w w^R over {a, b} (even-length palindromes). Needs nondeterminism: the machine must GUESS
    where the middle is (the epsilon move push -> pop), and BFS tries every guess."""
    d = {("push", c, EPS): [("push", c)] for c in "ab"}
    d[("push", EPS, EPS)] = [("pop", "")]
    for c in "ab":
        d[("pop", c, c)] = [("pop", "")]
    d[("pop", EPS, "$")] = [("acc", "$")]
    return PDA(d, "push", {"acc"})


def pda_more_a_than_b():
    """Words over {a, b} with more a's than b's (any order). The stack holds the surplus:
    A's if a's lead, B's if b's lead."""
    d = {}
    for top in ("$", "A"):
        d[("p", "a", top)] = [("p", "A" + top)]
    d[("p", "a", "B")] = [("p", "")]
    for top in ("$", "B"):
        d[("p", "b", top)] = [("p", "B" + top)]
    d[("p", "b", "A")] = [("p", "")]
    d[("p", EPS, "A")] = [("acc", "A")]
    return PDA(d, "p", {"acc"})


def is_anbn(w):
    n = len(w) // 2
    return len(w) % 2 == 0 and w == "a" * n + "b" * n


def is_balanced(w):
    depth = 0
    for c in w:
        depth += 1 if c == "(" else -1
        if depth < 0:
            return False
    return depth == 0


def is_even_palindrome(w):
    return len(w) % 2 == 0 and w == w[::-1]


def is_more_a(w):
    return w.count("a") > w.count("b")


# --------------------------------------------------------------------------- demo

def all_words(alphabet, max_len):
    """Every word over alphabet of length 0 .. max_len, shortest first."""
    return ["".join(p) for n in range(max_len + 1) for p in product(alphabet, repeat=n)]


def main():
    machines = [
        ("a^n b^n", pda_anbn(), is_anbn, "ab", ["", "ab", "aabb", "aab", "abab", "aaabbb"]),
        ("balanced ( )", pda_balanced(), is_balanced, "()", ["()", "(()())", "())(", "((("]),
        ("w w^R (even palindrome)", pda_even_palindrome(), is_even_palindrome, "ab",
         ["abba", "abab", "baaaab", "aa", "aba"]),
        ("#a > #b", pda_more_a_than_b(), is_more_a, "ab", ["a", "ab", "bbaaa", "babab", "bbaa"]),
    ]
    print("=" * 70)
    print("Pushdown automata (BFS over nondeterministic configurations)")
    print("=" * 70)
    for name, m, truth, alphabet, samples in machines:
        print(name)
        for w in samples:
            stats = {}
            print(f"  {w!r:10} -> {str(m.accepts(w, stats=stats)):5}  ({stats['configs']} configurations)")
        words = all_words(alphabet, 10)
        ok = all(m.accepts(w) == truth(w) for w in words)
        print(f"  agrees with the Python predicate on all {len(words)} words of length <= 10: {ok}\n")

    print("An accepting computation of the palindrome PDA on 'abba' (state, read, stack):")
    for state, pos, stack in pda_even_palindrome().run_trace("abba"):
        print(f"  {state:5} read {'abba'[:pos]!r:7} stack {stack}")
    print("  The move push -> pop happens after 'ab': the guessed middle.")


if __name__ == "__main__":
    main()
