#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-checks for the lambda-calculus interpreter.

Run with:   python -m unittest discover -s tests
       or:  python tests/test_lambda.py

Every check reduces a lambda term to its normal form with the normal-order
strategy and then reads the answer back (a Church numeral, a Church boolean,
or a list).  Nothing here uses Python's own arithmetic to decide the result --
the arithmetic happens inside the interpreter.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lambda_calculus as lc  # noqa: E402


# Definitions built on top of the bundled prelude, used by the tests.
EXTRA = r"""
FACT = Y (\f. \n. IF (IS_ZERO n) ONE (MULT n (f (PRED n))))
FIB  = Y (\f. \n. IF (IS_LESS_EQUAL n ONE) n (ADD (f (PRED n)) (f (PRED (PRED n)))))
RANGE = \m. \n. Y (\f. \k. IF (IS_EQUAL k n) (PAIR k NIL) (PAIR k (f (SUCC k)))) m
MAP = \g. \xs. Y (\f. \x. IF (IS_NIL x) NIL (PAIR (g (FST x)) (f (SND x)))) xs
SQUARE = \z. MULT z z
"""


def _environment():
    defs = {}
    runs = []
    lc.parse_program(lc.PRELUDE, defs, runs)
    lc.parse_program(EXTRA, defs, runs)
    return defs


_DEFS = _environment()


def normal_form(expr, max_steps=100_000):
    """Reduce a term (given as text) to normal form with the given defs."""
    term = lc.parse(expr)
    result, _, halted = lc.normalize(term, _DEFS, "normal", True, max_steps)
    if not halted:
        raise AssertionError(f"no normal form within {max_steps} steps: {expr}")
    return result


def as_int(expr):
    value = lc.church_numeral(normal_form(expr))
    assert value is not None, f"not a Church numeral: {expr}"
    return value


def as_bool(expr):
    value = lc.church_bool(normal_form(expr))
    assert value is not None, f"not a Church boolean: {expr}"
    return value


def as_list(expr):
    value = lc.church_list(normal_form(expr))
    assert value is not None, f"not a Church list: {expr}"
    return [lc.church_numeral(item) for item in value]


class TestBooleans(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(as_bool("TRUE"), "TRUE")
        self.assertEqual(as_bool("FALSE"), "FALSE")

    def test_gates(self):
        self.assertEqual(as_bool("AND TRUE FALSE"), "FALSE")
        self.assertEqual(as_bool("AND TRUE TRUE"), "TRUE")
        self.assertEqual(as_bool("OR FALSE TRUE"), "TRUE")
        self.assertEqual(as_bool("OR FALSE FALSE"), "FALSE")
        self.assertEqual(as_bool("NOT TRUE"), "FALSE")
        self.assertEqual(as_bool("NOT FALSE"), "TRUE")
        self.assertEqual(as_bool("XOR TRUE TRUE"), "FALSE")
        self.assertEqual(as_bool("XOR TRUE FALSE"), "TRUE")

    def test_if_selects(self):
        self.assertEqual(as_int("IF TRUE ONE TWO"), 1)
        self.assertEqual(as_int("IF FALSE ONE TWO"), 2)


class TestArithmetic(unittest.TestCase):
    def test_successor(self):
        self.assertEqual(as_int("SUCC TWO"), 3)

    def test_addition(self):
        self.assertEqual(as_int("ADD TWO THREE"), 5)

    def test_multiplication(self):
        self.assertEqual(as_int("MULT TWO THREE"), 6)

    def test_power(self):
        self.assertEqual(as_int("POWER TWO THREE"), 8)
        self.assertEqual(as_int("POWER THREE TWO"), 9)

    def test_predecessor(self):
        self.assertEqual(as_int("PRED THREE"), 2)
        self.assertEqual(as_int("PRED ZERO"), 0)

    def test_subtraction_saturates(self):
        self.assertEqual(as_int("SUB FIVE TWO"), 3)
        self.assertEqual(as_int("SUB TWO FIVE"), 0)


class TestComparison(unittest.TestCase):
    def test_is_zero(self):
        self.assertEqual(as_bool("IS_ZERO ZERO"), "TRUE")
        self.assertEqual(as_bool("IS_ZERO THREE"), "FALSE")

    def test_less_equal(self):
        self.assertEqual(as_bool("IS_LESS_EQUAL TWO THREE"), "TRUE")
        self.assertEqual(as_bool("IS_LESS_EQUAL THREE TWO"), "FALSE")
        self.assertEqual(as_bool("IS_LESS_EQUAL THREE THREE"), "TRUE")

    def test_equal(self):
        self.assertEqual(as_bool("IS_EQUAL THREE THREE"), "TRUE")
        self.assertEqual(as_bool("IS_EQUAL TWO THREE"), "FALSE")


class TestRecursion(unittest.TestCase):
    def test_factorial(self):
        self.assertEqual(as_int("FACT THREE"), 6)
        self.assertEqual(as_int("FACT FOUR"), 24)

    def test_fibonacci(self):
        self.assertEqual(as_int("FIB FIVE"), 5)
        self.assertEqual(as_int("FIB SIX"), 8)

    def test_let_rec_equals_y(self):
        self.assertEqual(
            as_int(r"let rec fact = \n. IF (IS_ZERO n) ONE "
                   r"(MULT n (fact (PRED n))) in fact THREE"),
            6,
        )


class TestLists(unittest.TestCase):
    def test_range(self):
        self.assertEqual(as_list("RANGE TWO FOUR"), [2, 3, 4])

    def test_car_cdr(self):
        self.assertEqual(as_int("FST (RANGE TWO FOUR)"), 2)
        self.assertEqual(as_int("FST (SND (RANGE TWO FOUR))"), 3)

    def test_map(self):
        self.assertEqual(as_list("MAP SQUARE (RANGE TWO THREE)"), [4, 9])


class TestSubstitution(unittest.TestCase):
    def test_alpha_renaming_avoids_capture(self):
        # (λx.λy.x) y  must yield  λy'.y : the argument y stays free.
        nf = normal_form(r"(\x. \y. x) y")
        self.assertIsInstance(nf, lc.Abs)
        self.assertNotEqual(nf.param, "y")          # the binder was renamed
        self.assertIn("y", lc.free_vars(nf))        # the free y survived
        self.assertEqual(nf.body, lc.Var("y"))

    def test_subst_is_capture_avoiding(self):
        renames = []
        result = lc.subst(lc.Abs("y", lc.Var("x")), "x", lc.Var("y"), renames)
        self.assertEqual(lc.free_vars(result), {"y"})
        self.assertTrue(renames)                    # a rename was reported


L = "\u03bb"


class TestParser(unittest.TestCase):
    def test_multi_argument_lambda(self):
        self.assertEqual(lc.pp(lc.parse(r"\x y z. x")),
                         f"{L}x.{L}y.{L}z.x")

    def test_application_is_left_associative(self):
        # f a b parses as ((f a) b), not (f (a b))
        self.assertEqual(lc.parse("f a b"),
                         lc.App(lc.App(lc.Var("f"), lc.Var("a")), lc.Var("b")))
        self.assertEqual(lc.pp(lc.parse("f a b")), "f a b")

    def test_let_sugar(self):
        self.assertEqual(
            lc.pp(lc.parse(r"let id = \x. x in id y")),
            f"({L}id.id y) ({L}x.x)",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
