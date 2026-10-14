#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lambda_calculus.py
==================

An interpreter for the (untyped) lambda calculus whose whole point is to
**show the complete computation process** -- every single reduction step.

What it does
------------
* Parses real lambda terms:      \\x. M   (or λx. M),   f x y,   (M)
* Also understands the "named" layer:
      name = term                       # a top-level definition
      let x = t in u                    # sugar for  (\\x. u) t
      let rec f = t in u                # sugar for  (\\f. u) (Y (\\f. t))
      let f x y = t in u                # multi-parameter sugar
* Performs **capture-avoiding** substitution.  When a substitution would
  capture a variable it renames it (alpha-conversion) and reports the rename.
* Reduces with a selectable strategy:
      normal  leftmost-outermost  (finds a normal form whenever one exists)
      cbn     call-by-name        (weak head normal form)
      cbv     call-by-value       (values are abstractions)
* Prints the reduction trace one step at a time.  A definition may be
  unfolded ("delta") so the trace stays readable, exactly like the
  hand-written derivations in the course notes (IF TRUE M N -> ... ).
* Recognises Church numerals / booleans / lists in the normal form and
  annotates the answer, e.g.   λf.λx. f (f (f x))   [= 3] .

Usage
-----
    python lambda_calculus.py                          # built-in demo
    python lambda_calculus.py examples/04_ycombinator.lc
    python lambda_calculus.py -e "(\\x.\\y.x) a b"      # inline term
    python lambda_calculus.py examples/02_numerals.lc --strategy cbv
    python lambda_calculus.py examples/02_numerals.lc --expand   # pure beta trace

Run `python lambda_calculus.py -h` for all options.  Standard library only.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Deep terms recurse deeply; give ourselves room.
sys.setrecursionlimit(1_000_000)


# ======================================================================
# 1. Abstract syntax
# ======================================================================
# A term is exactly one of the three lambda-calculus constructs:
#   Var  x          a variable
#   Abs  λx. body   an abstraction (function definition)
#   App  f a        an application (function call)
# The nodes are frozen so they are hashable -- we rely on that to fold a
# reduced term back into its name for display.


class Term:
    """Base class of all lambda terms."""


@dataclass(frozen=True)
class Var(Term):
    name: str

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Var({self.name})"


@dataclass(frozen=True)
class Abs(Term):
    param: str
    body: Term

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Abs({self.param}, {self.body!r})"


@dataclass(frozen=True)
class App(Term):
    fn: Term
    arg: Term

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"App({self.fn!r}, {self.arg!r})"


def make_abs(params: List[str], body: Term) -> Term:
    """Build \\a b c. body from ['a','b','c'] and body."""
    for p in reversed(params):
        body = Abs(p, body)
    return body


class ParseError(Exception):
    """Raised when a term cannot be parsed."""


# ======================================================================
# 2. Lexer
# ======================================================================

_TOKEN_RE = re.compile(
    r"""
      (?P<WS>\s+)
    | (?P<COMMENT>\#[^\n]*)
    | (?P<LAMBDA>[\\\u03bb])
    | (?P<DOT>\.)
    | (?P<LPAREN>\()
    | (?P<RPAREN>\))
    | (?P<EQ>=)
    | (?P<IDENT>[A-Za-z_][A-Za-z0-9_']*)
    | (?P<MISMATCH>.)
    """,
    re.VERBOSE,
)

_KEYWORDS = {"let": "LET", "rec": "REC", "in": "IN"}

_TOKEN_NAMES = {
    "LAMBDA": r"'\' or 'λ'",
    "DOT": "'.'",
    "LPAREN": "'('",
    "RPAREN": "')'",
    "EQ": "'='",
    "IDENT": "an identifier",
    "LET": "'let'",
    "REC": "'rec'",
    "IN": "'in'",
    "EOF": "end of input",
}


def tokenize(text: str) -> List[Tuple[str, str, int]]:
    tokens: List[Tuple[str, str, int]] = []
    for m in _TOKEN_RE.finditer(text):
        kind = m.lastgroup
        value = m.group()
        if kind in ("WS", "COMMENT"):
            continue
        if kind == "MISMATCH":
            raise ParseError(f"unexpected character {value!r} at position {m.start()}")
        if kind == "IDENT" and value in _KEYWORDS:
            kind = _KEYWORDS[value]
        tokens.append((kind, value, m.start()))
    tokens.append(("EOF", "", len(text)))
    return tokens


# ======================================================================
# 3. Parser  (recursive descent)
# ======================================================================
#
#   expr   ::= 'let' ['rec'] IDENT IDENT* ('=')? expr 'in' expr
#            | '\' IDENT+ '.' expr
#            | app
#   app    ::= atom atom*                 (left associative)
#   atom   ::= IDENT | '(' expr ')'


class Parser:
    def __init__(self, text: str):
        self.text = text
        self.tokens = tokenize(text)
        self.pos = 0

    # -- token helpers -------------------------------------------------
    def peek(self) -> Tuple[str, str, int]:
        return self.tokens[self.pos]

    def kind(self) -> str:
        return self.tokens[self.pos][0]

    def advance(self) -> Tuple[str, str, int]:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind: str) -> Tuple[str, str, int]:
        if self.kind() != kind:
            got = _TOKEN_NAMES.get(self.kind(), self.peek()[0])
            want = _TOKEN_NAMES.get(kind, kind)
            raise ParseError(
                f"expected {want} but found {got} {self.peek()[1]!r} "
                f"at position {self.peek()[2]}"
            )
        return self.advance()

    # -- grammar -------------------------------------------------------
    def parse(self) -> Term:
        term = self.parse_expr()
        if self.kind() != "EOF":
            raise ParseError(
                f"unexpected {self.peek()[1]!r} at position {self.peek()[2]} "
                f"(check parentheses)"
            )
        return term

    def parse_expr(self) -> Term:
        if self.kind() == "LET":
            return self.parse_let()
        if self.kind() == "LAMBDA":
            return self.parse_lambda()
        return self.parse_app()

    def parse_let(self) -> Term:
        self.expect("LET")
        recursive = False
        if self.kind() == "REC":
            self.advance()
            recursive = True
        name = self.expect("IDENT")[1]
        params: List[str] = []
        while self.kind() == "IDENT":
            params.append(self.advance()[1])
        if self.kind() == "EQ":
            self.advance()
        term = self.parse_expr()
        if params:
            term = make_abs(params, term)
        self.expect("IN")
        body = self.parse_expr()
        if recursive:
            # let rec f = t in u  ==>  (λf. u) (Y (λf. t))
            return App(Abs(name, body), App(Var("Y"), Abs(name, term)))
        # let f = t in u  ==>  (λf. u) t
        return App(Abs(name, body), term)

    def parse_lambda(self) -> Term:
        self.expect("LAMBDA")
        params = [self.expect("IDENT")[1]]
        while self.kind() == "IDENT":
            params.append(self.advance()[1])
        self.expect("DOT")
        body = self.parse_expr()
        return make_abs(params, body)

    def parse_app(self) -> Term:
        node = self.parse_atom()
        while self.kind() in ("IDENT", "LPAREN"):
            node = App(node, self.parse_atom())
        return node

    def parse_atom(self) -> Term:
        if self.kind() == "LPAREN":
            self.advance()
            node = self.parse_expr()
            self.expect("RPAREN")
            return node
        if self.kind() == "IDENT":
            return Var(self.advance()[1])
        got = _TOKEN_NAMES.get(self.kind(), self.peek()[0])
        raise ParseError(
            f"expected a variable or '(' but found {got} {self.peek()[1]!r} "
            f"at position {self.peek()[2]}"
        )


def parse(text: str) -> Term:
    """Parse a single lambda term."""
    return Parser(text).parse()


# ======================================================================
# 4. Free variables and capture-avoiding substitution
# ======================================================================

def free_vars(t: Term) -> set:
    if isinstance(t, Var):
        return {t.name}
    if isinstance(t, Abs):
        return free_vars(t.body) - {t.param}
    return free_vars(t.fn) | free_vars(t.arg)


def all_names(t: Term) -> set:
    if isinstance(t, Var):
        return {t.name}
    if isinstance(t, Abs):
        return {t.param} | all_names(t.body)
    return all_names(t.fn) | all_names(t.arg)


def _fresh(base: str, used: set) -> str:
    base = base.rstrip("'") or "v"
    name = base + "'"
    while name in used:
        name += "'"
    return name


def subst(t: Term, var: str, value: Term,
          renames: Optional[List[Tuple[str, str]]] = None) -> Term:
    """Capture-avoiding substitution  t[var := value].

    Whenever a binder would capture a free variable of ``value`` it is
    renamed; every rename is appended to ``renames`` so the driver can
    report the alpha-conversions that happened.
    """
    if renames is None:
        renames = []
    if isinstance(t, Var):
        return value if t.name == var else t
    if isinstance(t, Abs):
        if t.param == var:           # shadowed -- nothing to do
            return t
        if t.param in free_vars(value):
            used = all_names(t.body) | all_names(value) | {var}
            new_name = _fresh(t.param, used)
            renames.append((t.param, new_name))
            renamed_body = subst(t.body, t.param, Var(new_name), renames)
            return Abs(new_name, subst(renamed_body, var, value, renames))
        return Abs(t.param, subst(t.body, var, value, renames))
    return App(subst(t.fn, var, value, renames),
               subst(t.arg, var, value, renames))


def size(t: Term) -> int:
    if isinstance(t, Var):
        return 1
    if isinstance(t, Abs):
        return 1 + size(t.body)
    return 1 + size(t.fn) + size(t.arg)


# ======================================================================
# 5. Pretty printer
# ======================================================================

def pp(t: Term, sym: str = "\u03bb") -> str:
    """Print a term with the minimum number of parentheses."""
    if isinstance(t, Var):
        return t.name
    if isinstance(t, Abs):
        return f"{sym}{t.param}.{pp(t.body, sym)}"
    # application: parenthesise an abstraction in function position and
    # anything compound in argument position
    fn = pp(t.fn, sym)
    arg = pp(t.arg, sym)
    if isinstance(t.fn, Abs):
        fn = f"({fn})"
    if isinstance(t.arg, (Abs, App)):
        arg = f"({arg})"
    return f"{fn} {arg}"


# ======================================================================
# 6. Name expansion and folding
# ======================================================================

def expand(t: Term, defs: Dict[str, Term], stack: Optional[List[str]] = None) -> Term:
    """Replace every defined name by its definition (macro expansion).

    This is how the "named" syntax turns into a pure, name-free lambda
    term.  Cycles are rejected.
    """
    if stack is None:
        stack = []
    if isinstance(t, Var):
        if t.name in defs:
            if t.name in stack:
                raise ParseError(f"cyclic definition involving {t.name!r}")
            return expand(defs[t.name], defs, stack + [t.name])
        return t
    if isinstance(t, Abs):
        return Abs(t.param, expand(t.body, defs, stack))
    return App(expand(t.fn, defs, stack), expand(t.arg, defs, stack))


def fold(t: Term, foldmap: Dict[Term, str]) -> Term:
    """Replace whole sub-terms by their name, for readable output.

    ``foldmap`` maps a *normalised* definition to the name it was defined
    with, so a reduced term such as λf.λx.f (f x) can be shown again as TWO.
    """
    if not foldmap:
        return t
    if t in foldmap:
        return Var(foldmap[t])
    if isinstance(t, Abs):
        return Abs(t.param, fold(t.body, foldmap))
    if isinstance(t, App):
        return App(fold(t.fn, foldmap), fold(t.arg, foldmap))
    return t


# ======================================================================
# 7. Reduction
# ======================================================================

@dataclass
class StepInfo:
    rule: str      # 'β', 'δ', or 'β,α'
    detail: str    # human-readable description of the step


def _abbrev(text: str, limit: int = 48) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _contract(app: App) -> Tuple[Term, StepInfo]:
    """Contract the redex (λx.body) arg."""
    fn = app.fn
    assert isinstance(fn, Abs)
    renames: List[Tuple[str, str]] = []
    body = subst(fn.body, fn.param, app.arg, renames)
    rule = "β"
    detail = f"{fn.param} := {_abbrev(pp(app.arg))}"
    if renames:
        rule = "β,α"
        renamed = ", ".join(f"{a}→{b}" for a, b in renames)
        detail += f"   (α: {renamed})"
    return body, StepInfo(rule, detail)


def step_normal(t: Term, defs: Dict[str, Term], delta: bool) -> Optional[Tuple[Term, StepInfo]]:
    """Leftmost-outermost (normal order) reduction, one redex.

    Outer application redexes are tried first; if none is available we
    reduce the function part, then the argument part, and finally under a
    lambda (which is what makes this normal order).
    """
    if isinstance(t, Var):
        if delta and t.name in defs:
            return defs[t.name], StepInfo("δ", f"unfold {t.name}")
        return None
    if isinstance(t, Abs):
        inner = step_normal(t.body, defs, delta)
        if inner:
            return Abs(t.param, inner[0]), inner[1]
        return None
    # App
    if isinstance(t.fn, Abs):
        return _contract(t)
    if delta and isinstance(t.fn, Var) and t.fn.name in defs:
        return App(defs[t.fn.name], t.arg), StepInfo("δ", f"unfold {t.fn.name}")
    inner = step_normal(t.fn, defs, delta)
    if inner:
        return App(inner[0], t.arg), inner[1]
    inner = step_normal(t.arg, defs, delta)
    if inner:
        return App(t.fn, inner[0]), inner[1]
    return None


def step_cbn(t: Term, defs: Dict[str, Term], delta: bool) -> Optional[Tuple[Term, StepInfo]]:
    """Call-by-name: normal order but stop at a lambda (weak head form).

    Arguments are never reduced on their own; only the head is driven.
    """
    if isinstance(t, Var):
        if delta and t.name in defs:
            return defs[t.name], StepInfo("δ", f"unfold {t.name}")
        return None
    if isinstance(t, Abs):
        return None
    if isinstance(t.fn, Abs):
        return _contract(t)
    if delta and isinstance(t.fn, Var) and t.fn.name in defs:
        return App(defs[t.fn.name], t.arg), StepInfo("δ", f"unfold {t.fn.name}")
    inner = step_cbn(t.fn, defs, delta)
    if inner:
        return App(inner[0], t.arg), inner[1]
    return None


def _is_value(t: Term, defs: Dict[str, Term], delta: bool) -> bool:
    if isinstance(t, Abs):
        return True
    # a name that still has to be unfolded is not yet a value
    if isinstance(t, Var) and delta and t.name in defs:
        return False
    return False


def step_cbv(t: Term, defs: Dict[str, Term], delta: bool) -> Optional[Tuple[Term, StepInfo]]:
    """Call-by-value: reduce the operator to a value, then the operand,
    then contract.  Values are abstractions."""
    if isinstance(t, Var):
        if delta and t.name in defs:
            return defs[t.name], StepInfo("δ", f"unfold {t.name}")
        return None
    if isinstance(t, Abs):
        return None
    if not _is_value(t.fn, defs, delta):
        inner = step_cbv(t.fn, defs, delta)
        if inner:
            return App(inner[0], t.arg), inner[1]
        return None
    # operator is a value: it must be an abstraction to contract
    if isinstance(t.fn, Abs):
        if not _is_value(t.arg, defs, delta):
            inner = step_cbv(t.arg, defs, delta)
            if inner:
                return App(t.fn, inner[0]), inner[1]
            return None
        return _contract(t)
    return None


_STRATEGIES = {"normal": step_normal, "cbn": step_cbn, "cbv": step_cbv}


def normalize(t: Term, defs: Dict[str, Term], strategy: str = "normal",
              delta: bool = True, max_steps: int = 10_000) -> Tuple[Term, int, bool]:
    """Reduce to normal form (or until ``max_steps``).

    Returns (normal-form, steps-taken, halted) where *halted* is False when
    the step budget ran out before reaching a normal form.
    """
    stepper = _STRATEGIES[strategy]
    steps = 0
    while steps < max_steps:
        result = stepper(t, defs, delta)
        if result is None:
            return t, steps, True
        t, _ = result
        steps += 1
    return t, steps, False


# ======================================================================
# 8. Recognising Church encodings in a normal form
# ======================================================================

def church_bool(t: Term) -> Optional[str]:
    """λx.λy.x -> 'TRUE', λx.λy.y -> 'FALSE', anything else -> None."""
    if isinstance(t, Abs) and isinstance(t.body, Abs):
        first, second, body = t.param, t.body.param, t.body.body
        if body == Var(first):
            return "TRUE"
        if body == Var(second):
            return "FALSE"
    return None


def church_numeral(t: Term) -> Optional[int]:
    """Count the applications in λf.λx. f (f (... x)); None if not a numeral."""
    if not (isinstance(t, Abs) and isinstance(t.body, Abs)):
        return None
    f_name, x_name, body = t.param, t.body.param, t.body.body
    n = 0
    cur = body
    while isinstance(cur, App) and cur.fn == Var(f_name):
        n += 1
        cur = cur.arg
    if cur == Var(x_name):
        return n
    return None


def _church_nil(t: Term) -> bool:
    return isinstance(t, Abs) and church_bool(t.body) == "TRUE"


def _church_pair(t: Term) -> Optional[Tuple[Term, Term]]:
    """λf. f a b  -> (a, b)."""
    if isinstance(t, Abs):
        s = t.param
        body = t.body
        if (isinstance(body, App) and isinstance(body.fn, App)
                and body.fn.fn == Var(s)):
            return body.fn.arg, body.arg
    return None


def church_list(t: Term, depth: int = 0) -> Optional[List[Term]]:
    if depth > 1000:
        return None
    if _church_nil(t):
        return []
    pair = _church_pair(t)
    if pair is None:
        return None
    head, tail = pair
    rest = church_list(tail, depth + 1)
    if rest is None:
        return None
    return [head] + rest


def _elem_str(t: Term, sym: str) -> str:
    n = church_numeral(t)
    if n is not None:
        return str(n)
    b = church_bool(t)
    if b is not None:
        return b
    return pp(t, sym)


def describe(t: Term, sym: str = "\u03bb") -> Optional[str]:
    """A short human gloss for a normal form, or None if unrecognised.

    Church numerals and booleans overlap at zero (λf.λx.x is both 0 and
    FALSE), so we list every reading that fits.
    """
    parts: List[str] = []
    n = church_numeral(t)
    if n is not None:
        parts.append(str(n))
    b = church_bool(t)
    if b is not None:
        parts.append(b)
    lst = church_list(t)
    if lst:  # non-empty list only (empty == NIL, not worth a gloss)
        parts.append("[" + ", ".join(_elem_str(e, sym) for e in lst) + "]")
    if not parts:
        return None
    return " / ".join(parts)


# ======================================================================
# 9. Loading program files
# ======================================================================

_DEF_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_']*)\s*=\s*(.+)$")


def _strip_comment(line: str) -> str:
    idx = line.find("#")
    return line if idx < 0 else line[:idx]


def parse_program(text: str, defs: Dict[str, Term],
                  runs: List[Tuple[str, Term]]) -> None:
    """Read definitions and expressions from program text.

    A line is either
        name = term        a definition, or
        term               (optionally prefixed with 'run') an expression to evaluate.
    """
    for raw in text.splitlines():
        line = _strip_comment(raw).strip()
        if not line:
            continue
        match = _DEF_RE.match(line)
        if match:
            name, body = match.group(1), match.group(2).strip()
            defs[name] = parse(body)
            continue
        expr = line
        if expr.startswith("run"):
            expr = expr[3:].lstrip()
        runs.append((expr, parse(expr)))


def load_file(path: str, defs: Dict[str, Term],
              runs: List[Tuple[str, Term]], include_stack: Optional[List[str]] = None) -> None:
    path = os.path.abspath(path)
    if include_stack is None:
        include_stack = []
    if path in include_stack:
        return
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()

    lines: List[str] = []
    for raw in text.splitlines():
        line = _strip_comment(raw).strip()
        if line.startswith("include"):
            target = line[len("include"):].strip().strip('"').strip("'")
            load_file(os.path.join(os.path.dirname(path), target),
                      defs, runs, include_stack + [path])
        else:
            lines.append(raw)

    parse_program("\n".join(lines), defs, runs)


# ======================================================================
# 10. The prelude (auto-loaded unless --no-prelude)
# ======================================================================

PRELUDE = r"""
# ---------------------------------------------------------------------
# prelude.lc -- Church encodings shared by the examples
# (A term may be replaced by a name; the trace shows 'δ unfold NAME'.)
# ---------------------------------------------------------------------

# --- Booleans -------------------------------------------------------
TRUE  = \x. \y. x
FALSE = \x. \y. y
IF    = \c. \x. \y. c x y
AND   = \p. \q. p q p
OR    = \p. \q. p p q
NOT   = \c. c FALSE TRUE
XOR   = \p. \q. p (NOT q) q

# --- Pairs and lists ------------------------------------------------
PAIR   = \a. \b. \f. f a b
FST    = \p. p TRUE
SND    = \p. p FALSE
NIL    = \f. TRUE
IS_NIL = \p. p (\x. \y. FALSE)

# --- Fixpoint (used by 'let rec') -----------------------------------
Y = \f. (\x. f (x x)) (\x. f (x x))

# --- Church numerals ------------------------------------------------
ZERO = \f. \x. x
SUCC = \n. \f. \x. f (n f x)

# --- Arithmetic -----------------------------------------------------
ADD   = \m. \n. n SUCC m
MULT  = \m. \n. \f. m (n f)
POWER = \x. \y. y x
PRED  = \n. \f. \x. n (\g. \h. h (g f)) (\u. x) (\u. u)
SUB   = \m. \n. n PRED m

# --- Comparison -----------------------------------------------------
IS_ZERO       = \n. n (\x. FALSE) TRUE
IS_LESS_EQUAL = \m. \n. IS_ZERO (SUB m n)
IS_EQUAL      = \m. \n. AND (IS_LESS_EQUAL m n) (IS_LESS_EQUAL n m)

# --- Some numerals to play with -------------------------------------
ONE     = SUCC ZERO
TWO     = SUCC ONE
THREE   = SUCC TWO
FOUR    = SUCC THREE
FIVE    = SUCC FOUR
SIX     = SUCC FIVE
TEN     = MULT TWO FIVE
"""


# ======================================================================
# 11. Presentation
# ======================================================================

class Style:
    """Tiny ANSI helper.  Does nothing when colour is off."""

    def __init__(self, enabled: bool):
        self.enabled = enabled

    def _wrap(self, code: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def rule(self, text: str) -> str:
        return self._wrap("36", text)      # cyan

    def num(self, text: str) -> str:
        return self._wrap("2", text)       # dim

    def result(self, text: str) -> str:
        return self._wrap("1;32", text)    # bold green

    def head(self, text: str) -> str:
        return self._wrap("1", text)       # bold


def _resolve_color(flag: Optional[bool]) -> bool:
    if flag is not None:
        return flag
    # auto: colour only when attached to a real terminal
    try:
        return sys.stdout.isatty()
    except Exception:  # pragma: no cover
        return False


def _build_foldmap(defs: Dict[str, Term]) -> Dict[Term, str]:
    """Map *expanded* definitions back to their names, for readable output.

    The keys are the fully expanded (name-free) definitions, which is exactly
    the shape produced by --expand, so folding puts the names back into a pure
    trace.  Expansion is finite even for the Y combinator, so nothing blows up.
    """
    foldmap: Dict[Term, str] = {}
    for name, term in defs.items():
        try:
            expanded = expand(term, defs)
        except ParseError:
            continue
        if size(expanded) < 3:
            continue
        foldmap.setdefault(expanded, name)
    return foldmap


def _print_run(source: str, term: Term, defs: Dict[str, Term],
               args: argparse.Namespace, style: Style, sym: str,
               foldmap: Dict[Term, str], index: int) -> None:
    use_delta = not args.expand
    work = expand(term, defs) if args.expand else term

    width = 68
    title = f" {index}. {source} "
    print(style.head(title.center(width, "─")))

    if args.show_expanded:
        pure = expand(term, defs)
        shown = pp(fold(pure, foldmap), sym) if args.fold else pp(pure, sym)
        print(f"  {style.num('expanded :')} {shown}")
        print(f"  {style.num('strategy :')} {args.strategy}"
              f"   ({'delta on' if use_delta else 'pure beta'})")

    def show(t: Term) -> str:
        return pp(fold(t, foldmap), sym) if args.fold else pp(t, sym)

    current = work
    print(f"  {style.num('0'.rjust(4))}  {show(current)}")

    steps = 0
    halted = True
    overflow = False
    stepper = _STRATEGIES[args.strategy]
    while steps < args.max_steps:
        if size(current) > args.max_size:
            overflow = True
            break
        result = stepper(current, defs, use_delta)
        if result is None:
            break
        current, info = result
        steps += 1
        tag = style.rule(f"[{info.rule} {info.detail}]")
        if args.quiet:
            continue
        print(f"  {style.num(str(steps).rjust(4))}  {show(current)}   {tag}")
    else:
        halted = False

    print()
    if halted:
        gloss = describe(current, sym)
        answer = show(current)
        line = f"  {style.result('normal form')}  after {steps} reduction(s):  {answer}"
        if gloss:
            line += f"   {style.head('= ' + gloss)}"
        print(line)
    elif overflow:
        print(f"  {style.result('stopped')} -- the term grew past --max-size "
              f"({args.max_size}); it probably has no normal form.")
        print(f"    {show(current)}")
    else:
        print(f"  {style.result('stopped')} after {args.max_steps} steps "
              f"(increase --max-steps); last term:")
        print(f"    {show(current)}")
    print()


# ======================================================================
# 12. Command line
# ======================================================================

DEMO = [
    r"(\f. \x. f (f x)) (\y. ADD y y) TWO",
    r"IF TRUE ONE TWO",
    r"ADD TWO THREE",
    r"let twice = \f. \x. f (f x) in twice (\y. SUCC y)",
    r"let rec fact = \n. IF (IS_ZERO n) ONE (MULT n (fact (PRED n))) in fact THREE",
]


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A lambda-calculus interpreter that shows every reduction step.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage")[1] if "Usage" in __doc__ else None,
    )
    ap.add_argument("files", nargs="*", help="program files (.lc) to load and run")
    ap.add_argument("-e", "--eval", action="append", default=[],
                    metavar="TERM", help="evaluate a term given on the command line")
    ap.add_argument("--strategy", choices=["normal", "cbn", "cbv"],
                    default="normal", help="reduction strategy (default: normal)")
    ap.add_argument("--max-steps", type=int, default=3000,
                    help="maximum reduction steps per term (default: 3000)")
    ap.add_argument("--max-size", type=int, default=200_000,
                    help="bail out when a term grows past this many nodes "
                         "(default: 200000; guards against non-terminating terms)")
    ap.add_argument("--expand", action="store_true",
                    help="expand all names first: show a pure, name-free beta trace")
    ap.add_argument("--show-expanded", action="store_true",
                    help="also print the fully expanded term before reducing")
    ap.add_argument("--fold", dest="fold", action="store_true",
                    help="fold sub-terms back into their names for display "
                         "(most useful together with --expand)")
    ap.add_argument("--no-prelude", dest="prelude", action="store_false",
                    help="do not auto-load the bundled prelude.lc")
    ap.add_argument("--ascii", action="store_true",
                    help="write \\ instead of the unicode λ")
    ap.add_argument("--color", dest="color", action="store_true", default=None,
                    help="force coloured output")
    ap.add_argument("--no-color", dest="color", action="store_false",
                    help="disable coloured output")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="print only the final result of each term")
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    style = Style(_resolve_color(args.color))
    sym = "\\" if args.ascii else "\u03bb"

    defs: Dict[str, Term] = {}
    runs: List[Tuple[str, Term]] = []

    # the bundled prelude lives next to this file
    if args.prelude:
        prelude_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "prelude.lc")
        if os.path.exists(prelude_path):
            load_file(prelude_path, defs, runs)
        else:
            parse_program(PRELUDE, defs, runs)

    for path in args.files:
        load_file(path, defs, runs)

    if not args.files and not args.eval:
        for line in DEMO:
            runs.append((line, parse(line)))

    for line in args.eval:
        runs.append((line, parse(line)))

    if not runs:
        print("Nothing to do.  Pass a file, use -e/--eval, or run with no arguments "
              "for the built-in demo.")
        return 0

    foldmap = _build_foldmap(defs) if args.fold else {}

    if not args.quiet:
        print()
        print(style.head(f"lambda calculus \u2014 strategy {args.strategy}, "
                         f"{len(defs)} definitions loaded"))
        print()

    for index, (source, term) in enumerate(runs, start=1):
        _print_run(source, term, defs, args, style, sym, foldmap, index)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
