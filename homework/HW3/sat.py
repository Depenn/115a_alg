import re
import sys

OPS = {
    "and": "and",
    "or": "or",
    "not": "not",
    "&": "and",
    "|": "or",
    "~": "not",
}

VAR_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
NUM_RE = re.compile(r"(\d+)$")


def tokenize(expr):
    tokens = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c in " \t":
            i += 1
            continue
        if c in "()":
            tokens.append(c)
            i += 1
            continue
        m = VAR_RE.match(expr[i:])
        if m:
            word = m.group(0).lower()
            tokens.append(OPS.get(word, word))
            i += len(word)
            continue
        if c in "&|~":
            tokens.append(OPS[c])
            i += 1
            continue
        raise ValueError("unknown character: %r" % c)
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def parse(self):
        node = self.parse_or()
        if self.peek() is not None:
            raise ValueError("trailing token: %s" % self.peek())
        return node

    def parse_or(self):
        node = self.parse_and()
        while self.peek() == "or":
            self.advance()
            node = ("or", node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_not()
        while self.peek() == "and":
            self.advance()
            node = ("and", node, self.parse_not())
        return node

    def parse_not(self):
        if self.peek() == "not":
            self.advance()
            return ("not", self.parse_not())
        return self.parse_atom()

    def parse_atom(self):
        tok = self.peek()
        if tok == "(":
            self.advance()
            node = self.parse_or()
            if self.peek() != ")":
                raise ValueError("missing closing parenthesis")
            self.advance()
            return node
        if tok is None:
            raise ValueError("incomplete expression")
        if tok in ("and", "or", "not"):
            raise ValueError("operator without operand: %s" % tok)
        self.advance()
        return ("var", tok)


def parse(expr):
    return Parser(tokenize(expr)).parse()


def get_variables(ast):
    kind = ast[0]
    if kind == "var":
        return {ast[1]}
    if kind == "not":
        return get_variables(ast[1])
    return get_variables(ast[1]) | get_variables(ast[2])


def evaluate(ast, assignment):
    kind = ast[0]
    if kind == "var":
        return assignment[ast[1]]
    if kind == "not":
        return not evaluate(ast[1], assignment)
    left = evaluate(ast[1], assignment)
    if kind == "and" and not left:
        return False
    if kind == "or" and left:
        return True
    return evaluate(ast[2], assignment)


def natural_key(name):
    m = NUM_RE.search(name)
    return (int(m.group(1)) if m else 0, name)


def make_assignment(i, variables):
    n = len(variables)
    return {
        var: bool((i >> (n - 1 - k)) & 1)
        for k, var in enumerate(variables)
    }


def val_str(b):
    return "T" if b else "F"


def print_truth_table(variables, rows):
    result_col = "result"
    cols = variables + [result_col]
    widths = {c: max(len(c), 1) for c in cols}
    widths[result_col] = max(len(result_col), len(val_str(rows[0][1])))
    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("".ljust(widths[c], "-") for c in cols)
    print(header)
    print(sep)
    for assignment, value in rows:
        cells = [val_str(assignment[v]).ljust(widths[v]) for v in variables]
        cells.append(val_str(value).ljust(widths[result_col]))
        print(" | ".join(cells))


def main():
    formula = sys.argv[1] if len(sys.argv) > 1 else "(x1 or x2) and (~x1 or ~x2)"
    ast = parse(formula)
    variables = sorted(get_variables(ast), key=natural_key)
    n = len(variables)
    rows = []
    satisfying = []
    for i in range(1 << n):
        assignment = make_assignment(i, variables)
        value = evaluate(ast, assignment)
        rows.append((assignment, value))
        if value:
            satisfying.append(assignment)

    print("Formula :", formula)
    print("Variables:", ", ".join(variables))
    print("Enumerated assignments (2^%d = %d rows)" % (n, len(rows)))
    print()
    print_truth_table(variables, rows)
    print()
    if satisfying:
        print("SAT - the formula is satisfiable.")
        for assignment in satisfying:
            print("  ", ", ".join(
                "%s=%s" % (v, val_str(assignment[v])) for v in variables))
    else:
        print("UNSAT - the formula is not satisfiable.")


if __name__ == "__main__":
    main()