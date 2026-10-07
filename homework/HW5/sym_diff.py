"""Symbolic differentiation: parse an expression string into a tree, differentiate recursively."""

import math


def tokenize(s):
    tokens = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
        elif c.isdigit():
            j = i
            while j < n and (s[j].isdigit() or s[j] == "."):
                j += 1
            tokens.append(("num", float(s[i:j]) if "." in s[i:j] else int(s[i:j])))
            i = j
        elif c.isalpha():
            j = i
            while j < n and (s[j].isalnum() or s[j] == "_"):
                j += 1
            tokens.append(("id", s[i:j]))
            i = j
        elif c == "*" and i + 1 < n and s[i + 1] == "*":
            tokens.append(("op", "^"))
            i += 2
        elif c in "+-*/^()":
            tokens.append(("op", c))
            i += 1
        else:
            raise SyntaxError(f"unknown character {c!r}")
    tokens.append(("end", None))
    return tokens


class Parser:
    def __init__(self, text):
        self.tokens = tokenize(text)
        self.i = 0

    def peek(self):
        return self.tokens[self.i]

    def advance(self):
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def expect(self, value):
        tok = self.advance()
        if tok[1] != value:
            raise SyntaxError(f"expected {value!r}, got {tok[1]!r}")
        return tok

    def parse(self):
        return self.expr()

    def expr(self):
        left = self.term()
        while self.peek()[1] in ("+", "-"):
            op = self.advance()[1]
            left = (op, left, self.term())
        return left

    def term(self):
        left = self.factor()
        while self.peek()[1] in ("*", "/"):
            op = self.advance()[1]
            left = (op, left, self.factor())
        return left

    def factor(self):
        if self.peek()[1] == "-":
            self.advance()
            return ("neg", self.factor())
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek()[1] == "^":
            self.advance()
            return ("^", base, self.factor())
        return base

    def atom(self):
        tok = self.peek()
        if tok[0] == "num":
            self.advance()
            return tok[1]
        if tok[0] == "op" and tok[1] == "(":
            self.advance()
            inner = self.expr()
            self.expect(")")
            return inner
        if tok[0] == "id":
            self.advance()
            if self.peek()[0] == "op" and self.peek()[1] == "(":
                self.advance()
                arg = self.expr()
                self.expect(")")
                if tok[1] not in ("sin", "cos", "exp", "ln"):
                    raise SyntaxError(f"unknown function {tok[1]!r}")
                return (tok[1], arg)
            if tok[1] != "x":
                raise SyntaxError(f"unknown variable {tok[1]!r}")
            return tok[1]
        raise SyntaxError(f"unexpected token {tok!r}")


def parse(text):
    return Parser(text).parse()


def diff(e):
    """Recursively differentiate e with respect to x."""
    if isinstance(e, (int, float)):
        return 0
    if e == "x":
        return 1
    op = e[0]
    if op == "neg":
        return ("neg", diff(e[1]))
    if op == "+":
        return ("+", diff(e[1]), diff(e[2]))
    if op == "-":
        return ("-", diff(e[1]), diff(e[2]))
    if op == "*":
        return ("+", ("*", diff(e[1]), e[2]), ("*", e[1], diff(e[2])))
    if op == "/":
        return ("/",
                ("-", ("*", diff(e[1]), e[2]), ("*", e[1], diff(e[2]))),
                ("^", e[2], 2))
    if op == "^":
        u, v = e[1], e[2]
        return ("+",
                ("*", ("*", v, ("^", u, ("-", v, 1))), diff(u)),
                ("*", ("*", ("^", u, v), ("ln", u)), diff(v)))
    if op == "sin":
        return ("*", ("cos", e[1]), diff(e[1]))
    if op == "cos":
        return ("*", ("neg", ("sin", e[1])), diff(e[1]))
    if op == "exp":
        return ("*", ("exp", e[1]), diff(e[1]))
    if op == "ln":
        return ("/", diff(e[1]), e[1])
    raise ValueError(f"cannot differentiate {e!r}")


def simplify(e):
    if isinstance(e, (int, float)):
        return e
    if e == "x":
        return e
    op = e[0]
    if op in ("neg", "sin", "cos", "exp", "ln"):
        a = simplify(e[1])
        if op == "neg":
            if isinstance(a, (int, float)):
                return -a
            if isinstance(a, tuple) and a[0] == "neg":
                return a[1]
        return (op, a)
    a, b = simplify(e[1]), simplify(e[2])
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return a / b
        if op == "^":
            return a ** b
    if op == "+":
        if a == 0:
            return b
        if b == 0:
            return a
        if isinstance(b, tuple) and b[0] == "neg":
            return ("-", a, b[1])
    if op == "-":
        if a == b:
            return 0
        if b == 0:
            return a
        if isinstance(b, tuple) and b[0] == "neg":
            return ("+", a, b[1])
    if op == "*":
        if a == 0 or b == 0:
            return 0
        if a == 1:
            return b
        if b == 1:
            return a
    if op == "/":
        if a == 0:
            return 0
        if b == 1:
            return a
        if isinstance(a, tuple) and a[0] == "neg":
            return ("neg", ("/", a[1], b))
        if isinstance(a, (int, float)) and a < 0:
            return ("neg", ("/", -a, b))
    if op == "^":
        if b == 0:
            return 1
        if b == 1:
            return a
        if a == 0:
            return 0
    return (op, a, b)


PREC = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3, "neg": 4}


def to_str(e):
    if isinstance(e, (int, float)):
        return str(e)
    if e == "x":
        return "x"
    op = e[0]
    if op == "neg":
        return "-" + _wrap(e[1], 4)
    if op == "^":
        return _wrap(e[1], 4) + "^" + _wrap(e[2], 3)
    if op in PREC:
        return _wrap(e[1], PREC[op]) + " " + op + " " + _wrap(e[2], PREC[op] + 1)
    if op in ("sin", "cos", "exp", "ln"):
        return op + "(" + to_str(e[1]) + ")"
    raise ValueError(f"cannot print {e!r}")


def _wrap(e, min_prec):
    s = to_str(e)
    if isinstance(e, tuple) and e[0] in PREC and PREC[e[0]] < min_prec:
        return "(" + s + ")"
    return s


def evaluate(e, x):
    if isinstance(e, (int, float)):
        return e
    if e == "x":
        return x
    op = e[0]
    if op == "neg":
        return -evaluate(e[1], x)
    if op == "+":
        return evaluate(e[1], x) + evaluate(e[2], x)
    if op == "-":
        return evaluate(e[1], x) - evaluate(e[2], x)
    if op == "*":
        return evaluate(e[1], x) * evaluate(e[2], x)
    if op == "/":
        return evaluate(e[1], x) / evaluate(e[2], x)
    if op == "^":
        return evaluate(e[1], x) ** evaluate(e[2], x)
    if op == "sin":
        return math.sin(evaluate(e[1], x))
    if op == "cos":
        return math.cos(evaluate(e[1], x))
    if op == "exp":
        return math.exp(evaluate(e[1], x))
    if op == "ln":
        return math.log(evaluate(e[1], x))
    raise ValueError(e)


def sym_diff(text):
    return to_str(simplify(diff(parse(text))))


def diff_numeric(text, x, h=1e-6):
    f = parse(text)
    return (evaluate(f, x + h) - evaluate(f, x - h)) / (2 * h)


EXAMPLES = [
    "x^3 + 2*x",
    "sin(x) * x^2 + exp(x)",
    "(x^2 + 1) / (x - 1)",
    "cos(2*x)",
    "ln(x) + 1/x",
    "x^x",
]


def main():
    x = 0.7
    print(f"Numerical check at x = {x} via central finite differences (h = 1e-6)\n")
    for text in EXAMPLES:
        d = sym_diff(text)
        analytic = evaluate(simplify(diff(parse(text))), x)
        numeric = diff_numeric(text, x)
        rel = abs(analytic - numeric) / max(1e-9, abs(numeric))
        print(f"  f(x)  = {text}")
        print(f"  f'(x) = {d}")
        print(f"  f'({x}) analytic = {analytic:.10f} | numeric = {numeric:.10f} | rel.err = {rel:.2e}\n")


if __name__ == "__main__":
    main()