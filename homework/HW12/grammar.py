"""Formal grammars and the Chomsky hierarchy.

* Grammar.parse   - read rules like  "S -> a S b | a b"  (tokens separated by spaces,
                    a token that starts with an upper-case letter is a non-terminal, "ε" = empty)
* chomsky_type    - 3 regular / 2 context-free / 1 context-sensitive / 0 unrestricted
* generate        - random derivation (prints every sentential form if asked)
* language        - all words up to a given length (breadth-first over sentential forms)
* derivation      - shortest derivation of one word
* cyk             - CYK parsing for a grammar in Chomsky normal form, O(n^3)

Pure Python 3.  Run:  python grammar.py
"""
import random
import sys
from collections import deque

EMPTY = "ε"


def is_nonterminal(sym):
    return sym[:1].isupper()


class Grammar:
    def __init__(self, rules, start="S"):
        self.rules = [(tuple(l), tuple(r)) for l, r in rules]   # (lhs symbols, rhs symbols)
        self.start = start

    @classmethod
    def parse(cls, text, start="S"):
        rules = []
        for line in text.strip().splitlines():
            if not line.strip():
                continue
            lhs, rhs = line.split("->")
            for alt in rhs.split("|"):
                syms = [s for s in alt.split() if s != EMPTY]
                rules.append((lhs.split(), syms))
        return cls(rules, start)

    def __str__(self):
        return "\n".join(f"  {' '.join(l)} -> {' '.join(r) or EMPTY}" for l, r in self.rules)

    # ------------------------------------------------------------------ hierarchy
    def chomsky_type(self):
        """Most restrictive Chomsky type that the rules satisfy."""
        def right_linear(l, r):
            # A -> ε | a | a B   (one non-terminal on the left, at most one terminal then one NT)
            if len(l) != 1 or not is_nonterminal(l[0]):
                return False
            if len(r) == 0:
                return True
            if len(r) == 1:
                return not is_nonterminal(r[0])
            return len(r) == 2 and not is_nonterminal(r[0]) and is_nonterminal(r[1])

        def context_free(l, r):
            return len(l) == 1 and is_nonterminal(l[0])

        start_on_right = any(self.start in r for _, r in self.rules)

        def noncontracting(l, r):
            # |lhs| <= |rhs|; the only exception allowed is S -> ε when S never appears on a right side
            if len(r) == 0:
                return l == (self.start,) and not start_on_right
            return len(l) <= len(r) and any(map(is_nonterminal, l))

        if all(right_linear(l, r) for l, r in self.rules):
            return 3
        if all(context_free(l, r) for l, r in self.rules):
            return 2
        if all(noncontracting(l, r) for l, r in self.rules):
            return 1
        return 0

    # ------------------------------------------------------------------ derivations
    def successors(self, form):
        """All sentential forms reachable by one rule application (at any position)."""
        out = []
        for l, r in self.rules:
            k = len(l)
            for i in range(len(form) - k + 1):
                if form[i:i + k] == l:
                    out.append(form[:i] + r + form[i + k:])
        return out

    def generate(self, rng=None, max_steps=100, max_len=30, show=False):
        """Random derivation: at each step pick a random applicable (rule, position).
        Restarts if it gets stuck or too long. Returns the word as a string."""
        rng = rng or random.Random()
        while True:
            form = (self.start,)
            steps = [form]
            for _ in range(max_steps):
                if not any(map(is_nonterminal, form)):
                    if show:
                        for f in steps:
                            print("   ", " ".join(f) or EMPTY)
                    return " ".join(form)
                nxt = self.successors(form)
                if not nxt or len(form) > max_len:
                    break
                form = rng.choice(nxt)
                steps.append(form)

    def _bounded_forms(self, max_len):
        """BFS over sentential forms with at most max_len terminals and 2*max_len+2 symbols.
        For noncontracting grammars (types 1-3 without ε) this finds every word of length
        <= max_len; for the ε-rules used below it is also enough (checked in the tests)."""
        start = (self.start,)
        parent, todo = {start: None}, deque([start])
        while todo:
            form = todo.popleft()
            yield form, parent
            for nxt in self.successors(form):
                terminals = sum(1 for s in nxt if not is_nonterminal(s))
                if terminals <= max_len and len(nxt) <= 2 * max_len + 2 and nxt not in parent:
                    parent[nxt] = form
                    todo.append(nxt)

    def language(self, max_len):
        """Set of all words (strings, symbols joined without spaces) of length <= max_len."""
        return {"".join(f) for f, _ in self._bounded_forms(max_len)
                if not any(map(is_nonterminal, f))}

    def derivation(self, word):
        """Shortest derivation S => ... => word (list of forms), or None."""
        target = tuple(word)
        for form, parent in self._bounded_forms(len(word)):
            if form == target:
                path = []
                while form is not None:
                    path.append(form)
                    form = parent[form]
                return path[::-1]
        return None


# --------------------------------------------------------------------------- CYK

def cyk(cnf, word, start="S"):
    """CYK membership test. cnf: Grammar whose rules are A -> B C or A -> a.
    table[i][j] = set of non-terminals that derive word[i : i+j+1]. O(n^3 * |rules|)."""
    n = len(word)
    if n == 0:
        return any(l == (start,) and r == () for l, r in cnf.rules), []
    unit = [(l[0], r[0]) for l, r in cnf.rules if len(r) == 1]
    pair = [(l[0], r[0], r[1]) for l, r in cnf.rules if len(r) == 2]
    table = [[set() for _ in range(n)] for _ in range(n)]
    for i, c in enumerate(word):
        table[i][0] = {A for A, a in unit if a == c}
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            cell = table[i][length - 1]
            for split in range(1, length):
                left, right = table[i][split - 1], table[i + split][length - split - 1]
                for A, B, C in pair:
                    if B in left and C in right:
                        cell.add(A)
    return start in table[0][n - 1], table


# --------------------------------------------------------------------------- example grammars

G_ASTAR_BPLUS = Grammar.parse("""
S -> a S | b B | b
B -> b B | b
""")                                                         # a* b+          (type 3)

G_ANBN = Grammar.parse("S -> a S b | a b")                   # a^n b^n, n>=1  (type 2)

G_BALANCED = Grammar.parse("S -> ( S ) S | ε")               # balanced ( )   (type 2)

G_ANBNCN = Grammar.parse("""
S -> a b c | a S B c
c B -> B c
b B -> b b
""")                                                         # a^n b^n c^n    (type 1)
# a S B c adds one a, one B and one c; "c B -> B c" moves every B left past the c's,
# and "b B -> b b" turns it into b only once it touches the b block.

G_COPY = Grammar.parse("""
S -> T E
T -> a A T | b B T | ε
A a -> a A
A b -> b A
B a -> a B
B b -> b B
A E -> E a
B E -> E b
E -> ε
""")                                                         # w w, w in {a,b}*  (type 0)
# T writes w with a marker after each letter (a A b B ... E). Markers walk right over
# terminals (never over each other, so they keep their order); a marker next to the
# end-marker E becomes a terminal just after it, so the copy of w is rebuilt right to left.

G_EXPR = Grammar.parse("""
E -> E + T | T
T -> T * F | F
F -> ( E ) | x | y | 2
""", start="E")                                              # arithmetic expressions

G_ENGLISH = Grammar.parse("""
S -> NP VP
NP -> Det N | Det Adj N
VP -> V NP | V
Det -> the | a
Adj -> small | hungry
N -> cat | dog | student
V -> sees | chases | sleeps
""")

# Chomsky normal form versions for CYK
CNF_ANBN = Grammar.parse("""
S -> A X | A B
X -> S B
A -> a
B -> b
""")

CNF_BALANCED = Grammar.parse("""
S -> S S | L R | L Y
Y -> S R
L -> (
R -> )
""")


def is_anbncn(w):
    n = len(w) // 3
    return len(w) % 3 == 0 and w == "a" * n + "b" * n + "c" * n


def is_copy(w):
    h = len(w) // 2
    return len(w) % 2 == 0 and w[:h] == w[h:]


# --------------------------------------------------------------------------- demo

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")      # "ε" on a Windows console
    rng = random.Random(12)
    grammars = [
        ("a* b+", G_ASTAR_BPLUS, 6),
        ("a^n b^n", G_ANBN, 8),
        ("balanced ( )", G_BALANCED, 6),
        ("a^n b^n c^n", G_ANBNCN, 9),
        ("w w (copy language)", G_COPY, 6),
    ]
    print("=" * 70)
    print("1. Chomsky type of each grammar and its language (all words up to a length)")
    print("=" * 70)
    for name, g, L in grammars:
        words = sorted(g.language(L), key=lambda w: (len(w), w))
        print(f"{name}  -> type {g.chomsky_type()}")
        print(g)
        print(f"  words of length <= {L} ({len(words)}): {', '.join(w or EMPTY for w in words)}\n")

    print("=" * 70)
    print("2. Derivations")
    print("=" * 70)
    for name, g, w in [("a^n b^n c^n", G_ANBNCN, "aabbcc"), ("w w", G_COPY, "abab")]:
        path = g.derivation(w)
        print(f"{name}: shortest derivation of {w!r} ({len(path) - 1} steps)")
        print("   " + "\n=> ".join(" ".join(f) or EMPTY for f in path))
        print()

    print("=" * 70)
    print("3. Random generation")
    print("=" * 70)
    print(f"arithmetic expressions (type {G_EXPR.chomsky_type()}):")
    for _ in range(5):
        print("  ", G_EXPR.generate(rng, max_len=12))
    print(f"toy English (type {G_ENGLISH.chomsky_type()}):")
    for _ in range(5):
        print("  ", G_ENGLISH.generate(rng))
    print("one random derivation of a^n b^n c^n:")
    G_ANBNCN.generate(random.Random(0), show=True)
    print()

    print("=" * 70)
    print("4. CYK parsing (Chomsky normal form, dynamic programming O(n^3))")
    print("=" * 70)
    for g, words in [(CNF_ANBN, ["aabb", "aaabbb", "aabbb", "abab"]),
                     (CNF_BALANCED, ["(())()", "(()", "()()()", ")("])]:
        for w in words:
            print(f"  {w!r:10} -> {cyk(g, w)[0]}")
    ok, table = cyk(CNF_ANBN, "aabb")
    print("\n  CYK table for 'aabb' (row = substring length, column = start index):")
    for length in range(1, 5):
        cells = [",".join(sorted(table[i][length - 1])) or "-" for i in range(5 - length)]
        print(f"   len {length}: " + "  ".join(f"{c:5}" for c in cells))


if __name__ == "__main__":
    main()
