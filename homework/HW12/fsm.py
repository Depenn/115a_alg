"""Finite state machines (Chomsky type 3: regular languages).

* DFA  - deterministic finite automaton: run, trace, complete, minimize (Moore).
* NFA  - nondeterministic automaton with epsilon moves; subset construction -> DFA.
* anbn_counterexample - pigeonhole argument: ANY DFA is wrong on some a^i b^i.

Pure Python 3.  Run:  python fsm.py
"""
from collections import deque

EPS = ""          # label of an epsilon (empty) move in an NFA
DEAD = "dead"     # name of the sink state added by DFA.complete()


class DFA:
    def __init__(self, states, alphabet, delta, start, finals):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.delta = dict(delta)          # (state, symbol) -> state
        self.start = start
        self.finals = set(finals)

    def run(self, word):
        """State reached after reading word, or None if a transition is missing."""
        q = self.start
        for c in word:
            q = self.delta.get((q, c))
            if q is None:
                return None
        return q

    def accepts(self, word):
        return self.run(word) in self.finals

    def trace(self, word):
        """List of states visited, e.g. ['q0', 'q1', 'q0']."""
        path = [self.start]
        for c in word:
            nxt = self.delta.get((path[-1], c))
            if nxt is None:
                return path + [None]
            path.append(nxt)
        return path

    def complete(self):
        """Same language, but every (state, symbol) has a transition (missing ones go to DEAD)."""
        delta = dict(self.delta)
        states = set(self.states)
        missing = [(q, a) for q in self.states for a in self.alphabet if (q, a) not in delta]
        if missing:
            states.add(DEAD)
            for q, a in missing:
                delta[(q, a)] = DEAD
            for a in self.alphabet:
                delta[(DEAD, a)] = DEAD
        return DFA(states, self.alphabet, delta, self.start, self.finals)

    def reachable(self):
        seen, todo = {self.start}, deque([self.start])
        while todo:
            q = todo.popleft()
            for a in sorted(self.alphabet):
                r = self.delta.get((q, a))
                if r is not None and r not in seen:
                    seen.add(r)
                    todo.append(r)
        return seen

    def minimize(self):
        """Moore's partition refinement. Returns the minimal complete DFA (states 0, 1, ...)."""
        d = self.complete()
        states = sorted(d.reachable(), key=str)
        alphabet = sorted(d.alphabet)
        # start with two blocks: final / non-final
        block = {q: int(q in d.finals) for q in states}
        while True:
            # signature = own block + blocks of all successors
            sig = {q: (block[q],) + tuple(block[d.delta[(q, a)]] for a in alphabet) for q in states}
            ids = {}
            new_block = {q: ids.setdefault(sig[q], len(ids)) for q in states}
            if len(ids) == len(set(block.values())):
                break
            block = new_block
        # renumber so the start state is 0 (BFS order) - gives a canonical result
        order, todo = {}, deque([block[d.start]])
        rep = {}
        for q in states:
            rep.setdefault(block[q], q)
        while todo:
            b = todo.popleft()
            if b in order:
                continue
            order[b] = len(order)
            for a in alphabet:
                todo.append(block[d.delta[(rep[b], a)]])
        delta = {(order[block[q]], a): order[block[d.delta[(q, a)]]] for q in states for a in alphabet}
        finals = {order[block[q]] for q in states if q in d.finals}
        return DFA(set(order.values()), alphabet, delta, 0, finals)

    def __len__(self):
        return len(self.states)


class NFA:
    def __init__(self, states, alphabet, delta, start, finals):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.delta = {k: set(v) for k, v in delta.items()}   # (state, symbol or EPS) -> set
        self.start = start
        self.finals = set(finals)

    def eps_closure(self, S):
        S, todo = set(S), list(S)
        while todo:
            q = todo.pop()
            for r in self.delta.get((q, EPS), ()):
                if r not in S:
                    S.add(r)
                    todo.append(r)
        return frozenset(S)

    def step(self, S, c):
        return self.eps_closure({r for q in S for r in self.delta.get((q, c), ())})

    def accepts(self, word):
        S = self.eps_closure({self.start})
        for c in word:
            S = self.step(S, c)
            if not S:
                return False
        return bool(S & self.finals)

    def to_dfa(self):
        """Subset construction: each DFA state is a set of NFA states (only reachable ones)."""
        start = self.eps_closure({self.start})
        names, todo, delta = {start: 0}, deque([start]), {}
        while todo:
            S = todo.popleft()
            for a in sorted(self.alphabet):
                T = self.step(S, a)
                if T not in names:
                    names[T] = len(names)
                    todo.append(T)
                delta[(names[S], a)] = names[T]
        finals = {i for S, i in names.items() if S & self.finals}
        return DFA(set(names.values()), self.alphabet, delta, 0, finals)

    def __len__(self):
        return len(self.states)


# --------------------------------------------------------------------------- examples

def dfa_a_star():
    """a*  (any number of a's)."""
    return DFA({"q0"}, "a", {("q0", "a"): "q0"}, "q0", {"q0"})


def dfa_a_star_b_plus():
    """a* b+  (some a's, then at least one b)."""
    delta = {("A", "a"): "A", ("A", "b"): "B", ("B", "b"): "B"}
    return DFA({"A", "B"}, "ab", delta, "A", {"B"})


def dfa_even_zeros():
    """Binary strings with an even number of 0s."""
    delta = {("E", "0"): "O", ("E", "1"): "E", ("O", "0"): "E", ("O", "1"): "O"}
    return DFA({"E", "O"}, "01", delta, "E", {"E"})


def dfa_div_by(m):
    """Binary numbers (MSB first) divisible by m. State r = value mod m; reading bit b: r -> 2r+b."""
    delta = {(r, b): (2 * r + int(b)) % m for r in range(m) for b in "01"}
    return DFA(set(range(m)), "01", delta, 0, {0})


def dfa_a_count_mod4_even():
    """Even number of a's, built wastefully with 4 states (count mod 4). Minimizes to 2 states."""
    delta = {(r, "a"): (r + 1) % 4 for r in range(4)}
    delta.update({(r, "b"): r for r in range(4)})
    return DFA(set(range(4)), "ab", delta, 0, {0, 2})


def nfa_kth_from_end_is_1(k):
    """Strings over {0,1} whose k-th symbol from the end is 1. NFA: k+1 states (guess the position)."""
    delta = {(0, "0"): {0}, (0, "1"): {0, 1}}
    for i in range(1, k):
        delta[(i, "0")] = {i + 1}
        delta[(i, "1")] = {i + 1}
    return NFA(set(range(k + 1)), "01", delta, 0, {k})


def nfa_contains(pattern, alphabet="ab"):
    """Strings that contain pattern as a substring, with an epsilon move into the 'matching' chain."""
    n = len(pattern)
    delta = {("s", c): {"s"} for c in alphabet}
    delta[("s", EPS)] = {0}
    for i, c in enumerate(pattern):
        delta.setdefault((i, c), set()).add(i + 1)
    for c in alphabet:
        delta.setdefault((n, c), set()).add(n)
    return NFA({"s"} | set(range(n + 1)), alphabet, delta, "s", {n})


def dfa_anbn_upto(k):
    """A DFA that recognises a^n b^n correctly for n <= k only (2k+2 states plus a dead state)."""
    delta = {}
    for i in range(k):                      # ("a", i): read i a's
        delta[(("a", i), "a")] = ("a", i + 1)
    for i in range(1, k + 1):               # ("b", j): j more b's needed
        delta[(("a", i), "b")] = ("b", i - 1)
    for j in range(1, k):
        delta[(("b", j), "b")] = ("b", j - 1)
    states = {("a", i) for i in range(k + 1)} | {("b", j) for j in range(k)}
    return DFA(states, "ab", delta, ("a", 0), {("a", 0), ("b", 0)})


def is_anbn(w):
    n = len(w) // 2
    return len(w) % 2 == 0 and w == "a" * n + "b" * n


def anbn_counterexample(dfa):
    """Pigeonhole proof that a^n b^n is not regular, made concrete for one DFA.

    The (complete) DFA has N states, so among a^0, a^1, ..., a^N two prefixes a^i and a^j (i < j)
    end in the same state. Then a^i b^i and a^j b^i end in the same state too, so the DFA gives
    both the same answer - but only a^i b^i is in the language. Returns the word it gets wrong.
    """
    d = dfa.complete()
    first_seen = {}
    for j in range(len(d) + 1):
        q = d.run("a" * j)
        if q in first_seen:
            i = first_seen[q]
            for w in ("a" * i + "b" * i, "a" * j + "b" * i):
                if d.accepts(w) != is_anbn(w):
                    return w, i, j
        first_seen.setdefault(q, j)
    raise AssertionError("unreachable: pigeonhole always finds a collision")


# --------------------------------------------------------------------------- demo

def _show(name, m, words):
    print(f"{name}  ({len(m)} states)")
    for w in words:
        print(f"  {w!r:12} -> {str(m.accepts(w)):5}  path {' '.join(map(str, m.trace(w)))}"
              if isinstance(m, DFA) else f"  {w!r:12} -> {m.accepts(w)}")
    print()


def main():
    print("=" * 70)
    print("1. DFA examples")
    print("=" * 70)
    _show("a*", dfa_a_star(), ["", "aaa", "aab"])
    _show("a* b+", dfa_a_star_b_plus(), ["a", "aab", "aabaa", "abbb"])
    _show("even number of 0s", dfa_even_zeros(), ["010", "101", "10100", "1010010"])
    m3 = dfa_div_by(3)
    _show("binary divisible by 3", m3, ["0", "11", "110", "1001", "1010"])
    print("  check: every n < 1000 ->",
          all(m3.accepts(bin(n)[2:]) == (n % 3 == 0) for n in range(1000)))
    print()

    print("=" * 70)
    print("2. NFA with epsilon moves, subset construction")
    print("=" * 70)
    n = nfa_contains("aba")
    _show("contains 'aba' (NFA)", n, ["ab", "aaba", "bbabab", "abba"])
    d = n.to_dfa()
    print(f"  subset construction -> DFA with {len(d)} states,"
          f" minimized -> {len(d.minimize())} states\n")
    print("  k-th symbol from the end is 1:")
    print("   k | NFA states | DFA states (subset) | minimal DFA")
    for k in range(1, 11):
        nk = nfa_kth_from_end_is_1(k)
        dk = nk.to_dfa()
        print(f"  {k:2} | {len(nk.states):10} | {len(dk):19} | {len(dk.minimize()):11}")
    print("  -> the DFA needs 2^k states: the NFA is exponentially smaller.\n")

    print("=" * 70)
    print("3. DFA minimization (Moore partition refinement)")
    print("=" * 70)
    big = dfa_a_count_mod4_even()
    small = big.minimize()
    print(f"  'even number of a' built with {len(big)} states -> minimal DFA has {len(small)} states")
    print(f"  minimal transitions: {sorted(small.delta.items())}, finals {small.finals}")
    for m in (2, 3, 5, 6, 8):
        print(f"  divisible by {m}: {m} states -> minimal {len(dfa_div_by(m).minimize())}")
    print()

    print("=" * 70)
    print("4. a^n b^n is not regular: a pigeonhole counterexample for every DFA")
    print("=" * 70)
    for k in (1, 3, 5, 8):
        m = dfa_anbn_upto(k)
        w, i, j = anbn_counterexample(m)
        print(f"  DFA correct up to n={k} ({len(m.complete())} states): a^{i} and a^{j} reach the"
              f" same state -> wrong on {w!r} (says {m.accepts(w)}, truth {is_anbn(w)})")
    print("  More states only move the error further out; it never disappears.")


if __name__ == "__main__":
    main()
