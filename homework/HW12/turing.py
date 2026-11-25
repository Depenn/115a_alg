"""Turing machines (Chomsky type 0: recursively enumerable languages).

The tape is a dict {position: symbol}, so it is unbounded in both directions. A machine halts
when no transition applies: it accepts if it is then in an accept state, otherwise it rejects.
run() takes a step limit, because in general we cannot know in advance whether a machine halts
(the halting problem); hitting the limit gives the status "timeout", not an answer.

Pure Python 3.  Run:  python turing.py
"""
from collections import namedtuple

Result = namedtuple("Result", "status steps tape history")


class TuringMachine:
    def __init__(self, delta, start, accept, blank="_"):
        # delta: (state, read symbol) -> (new state, write symbol, move)  with move in L / R / S
        self.delta = dict(delta)
        self.start = start
        self.accept = set(accept)
        self.blank = blank

    def run(self, word, max_steps=100_000, trace=False):
        tape = {i: c for i, c in enumerate(word)}
        state, head, steps = self.start, 0, 0
        history = []
        while True:
            if trace:
                history.append((state, self._show(tape, head)))
            sym = tape.get(head, self.blank)
            if (state, sym) not in self.delta:
                status = "accept" if state in self.accept else "reject"
                return Result(status, steps, self._show(tape), history)
            if steps >= max_steps:
                return Result("timeout", steps, self._show(tape), history)
            state, write, move = self.delta[(state, sym)]
            tape[head] = write
            head += {"L": -1, "R": 1, "S": 0}[move]
            steps += 1

    def _show(self, tape, head=None):
        """Tape contents between the outermost non-blank cells; the head cell as [x]."""
        used = [i for i, c in tape.items() if c != self.blank]
        if head is not None:
            used.append(head)
        if not used:
            return ""
        cells = []
        for i in range(min(used), max(used) + 1):
            c = tape.get(i, self.blank)
            cells.append(f"[{c}]" if i == head else c)
        return "".join(cells)

    def accepts(self, word, max_steps=100_000):
        return self.run(word, max_steps).status == "accept"

    def output(self, word, max_steps=100_000):
        """For machines that compute a function: the tape left after halting (blanks trimmed)."""
        r = self.run(word, max_steps)
        assert r.status == "accept", r.status
        return r.tape.strip(self.blank)


def table(rules):
    """Build delta from lines 'state read -> new write move'."""
    delta = {}
    for line in rules.strip().splitlines():
        left, right = line.split("->")
        q, a = left.split()
        p, b, m = right.split()
        delta[(q, a)] = (p, b, m)
    return delta


# --------------------------------------------------------------------------- deciders

def tm_anbncn():
    """a^n b^n c^n, n >= 0. Each round crosses off one a (X), one b (Y) and one c (Z)."""
    return TuringMachine(table("""
        q0 a -> q1 X R
        q0 Y -> q4 Y R
        q0 _ -> acc _ S
        q1 a -> q1 a R
        q1 Y -> q1 Y R
        q1 b -> q2 Y R
        q2 b -> q2 b R
        q2 Z -> q2 Z R
        q2 c -> q3 Z L
        q3 a -> q3 a L
        q3 b -> q3 b L
        q3 Y -> q3 Y L
        q3 Z -> q3 Z L
        q3 X -> q0 X R
        q4 Y -> q4 Y R
        q4 Z -> q4 Z R
        q4 _ -> acc _ S
    """), "q0", {"acc"})


def tm_palindrome():
    """Palindromes over {a, b}: erase the first symbol, run to the end, compare with the last."""
    return TuringMachine(table("""
        q0 _ -> acc _ S
        q0 a -> ra _ R
        q0 b -> rb _ R
        ra a -> ra a R
        ra b -> ra b R
        ra _ -> ca _ L
        rb a -> rb a R
        rb b -> rb b R
        rb _ -> cb _ L
        ca a -> back _ L
        ca _ -> acc _ S
        cb b -> back _ L
        cb _ -> acc _ S
        back a -> back a L
        back b -> back b L
        back _ -> q0 _ R
    """), "q0", {"acc"})


# --------------------------------------------------------------------------- functions

def tm_binary_increment():
    """n -> n + 1 in binary. Go to the last bit, then add 1 with carry going left."""
    return TuringMachine(table("""
        right 0 -> right 0 R
        right 1 -> right 1 R
        right _ -> carry _ L
        carry 1 -> carry 0 L
        carry 0 -> done 1 S
        carry _ -> done 1 S
    """), "right", {"done"})


def tm_unary_add():
    """1^m + 1^n -> 1^(m+n): turn '+' into 1, then erase the last 1."""
    return TuringMachine(table("""
        q0 1 -> q0 1 R
        q0 + -> q1 1 R
        q1 1 -> q1 1 R
        q1 _ -> q2 _ L
        q2 1 -> done _ S
    """), "q0", {"done"})


# --------------------------------------------------------------------------- busy beavers

def busy_beaver(n):
    """Known champions for n = 2, 3, 4 states (2 symbols, blank 0, halt state H).
    n = 2 and 4 are the machines with the most steps S(n); for n = 3 the one with most 1s."""
    rules = {
        2: "A 0 -> B 1 R\nA 1 -> B 1 L\nB 0 -> A 1 L\nB 1 -> H 1 R",
        3: "A 0 -> B 1 R\nA 1 -> H 1 R\nB 0 -> C 0 R\nB 1 -> B 1 R\nC 0 -> C 1 L\nC 1 -> A 1 L",
        4: ("A 0 -> B 1 R\nA 1 -> B 1 L\nB 0 -> A 1 L\nB 1 -> C 0 L\n"
            "C 0 -> H 1 R\nC 1 -> D 1 L\nD 0 -> D 1 R\nD 1 -> A 0 R"),
    }[n]
    return TuringMachine(table(rules), "A", {"H"}, blank="0")


# --------------------------------------------------------------------------- halting

def tm_walk_right_forever():
    return TuringMachine({("q", "_"): ("q", "_", "R")}, "q", set())


def tm_skip_ones():
    """Moves right over a block of 1s and halts on the first blank: 1^k takes exactly k steps."""
    return TuringMachine(table("q 1 -> q 1 R"), "q", {"q"})


def halts_within(machine, word, budget):
    """A 'halting tester' that just runs the machine for budget steps. It can only ever answer
    'halts' or 'don't know'; for any budget there is an input on which it is wrong."""
    return machine.run(word, max_steps=budget).status != "timeout"


# --------------------------------------------------------------------------- demo

def is_anbncn(w):
    n = len(w) // 3
    return len(w) % 3 == 0 and w == "a" * n + "b" * n + "c" * n


def main():
    print("=" * 70)
    print("1. Decider for a^n b^n c^n (not context-free)")
    print("=" * 70)
    m = tm_anbncn()
    for w in ["", "abc", "aabbcc", "aabbc", "abcabc", "acb", "aaabbbccc"]:
        r = m.run(w)
        print(f"  {w!r:12} -> {r.status:6}  {r.steps:3} steps   final tape {r.tape}")
    print("\n  step-by-step on 'abc' (state, tape with [head]):")
    for state, tape in m.run("abc", trace=True).history:
        print(f"    {state:4} {tape}")
    print("\n  steps grow like n^2 (the head sweeps back and forth once per round):")
    print("     n | steps | steps / n^2")
    for n in (1, 2, 4, 8, 16, 32, 64):
        s = m.run("a" * n + "b" * n + "c" * n).steps
        print(f"   {n:3} | {s:5} | {s / n ** 2:.2f}")
    print()

    print("=" * 70)
    print("2. Palindromes over {a, b}")
    print("=" * 70)
    p = tm_palindrome()
    for w in ["", "a", "abba", "abab", "aabaa", "abbab"]:
        r = p.run(w)
        print(f"  {w!r:8} -> {r.status:6} {r.steps:3} steps")
    print()

    print("=" * 70)
    print("3. Machines that compute functions")
    print("=" * 70)
    inc = tm_binary_increment()
    for n in (0, 1, 5, 7, 11, 255):
        b = bin(n)[2:]
        print(f"  increment {b:>8} -> {inc.output(b):>9}   ({n} + 1 = {int(inc.output(b), 2)})")
    add = tm_unary_add()
    for m_, n_ in ((2, 3), (0, 4), (5, 0)):
        w = "1" * m_ + "+" + "1" * n_
        print(f"  unary add {w:>9} -> {add.output(w):<8} ({m_} + {n_} = {len(add.output(w))})")
    print()

    print("=" * 70)
    print("4. Busy beavers (start on an all-0 tape)")
    print("=" * 70)
    print("  states | steps until halt | 1s left on the tape")
    for n in (2, 3, 4):
        r = busy_beaver(n).run("")
        print(f"  {n:6} | {r.steps:16} | {r.tape.count('1'):5}   tape {r.tape}")
    print()

    print("=" * 70)
    print("5. Halting: a step budget is not a halting decider")
    print("=" * 70)
    r = tm_walk_right_forever().run("", max_steps=1000)
    print(f"  walk-right-forever after 1000 steps: {r.status} (it never halts, but a simulator"
          f" cannot tell 'never' from 'not yet')")
    for budget in (10, 100, 1000):
        w = "1" * (budget + 1)
        guess = halts_within(tm_skip_ones(), w, budget)
        r = tm_skip_ones().run(w, max_steps=10 * budget)
        print(f"  budget {budget:4}: input 1^{budget + 1} -> tester says halts={guess},"
              f" truth: halts after {r.steps} steps")


if __name__ == "__main__":
    main()
