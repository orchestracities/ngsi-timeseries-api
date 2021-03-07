from sql.ast.terms import *


def test_tree_of_ints():
    term = (lit(1) & 2) > 3
    expected = '((1 and 2) > 3)'
    assert expected == term.eval()


def test_tree_with_var():
    term = ((lit(1) & 2) > 3) | (var('x') == 'x')
    expected = "(((1 and 2) > 3) or (x = 'x'))"
    assert expected == term.eval()


def test_tree_with_null():
    term = ((lit(1) & None) > 3) | (var('x') == 'x')
    expected = "(((1 and null) > 3) or (x = 'x'))"
    assert expected == term.eval()


def test_tree_with_empty_string():
    term = ((lit(1) & '') > 3) | (var('x') == 'x')
    expected = "(((1 and '') > 3) or (x = 'x'))"
    assert expected == term.eval()


def test_ops_precedence_mystery():
    term = var('x') == lit(3) & var('y') > 'wada wada'
    expected = "((3 and y) > 'wada wada')"
    assert expected == term.eval()
# NOTE. Weird evaluation.
# I wasn't expecting the x term to vanish into thin air, but that's what's
# happening! Debugging into the test shows this is how the expression gets
# reduced:
#           3 & y
#           x = (3 & y)
#           (3 & y) > 'wada wada'
#
# Bottom line: use parentheses!


def test_and_binds_tighter_than_gt():
    term = (var('x') == 3) & var('y') > 'wada wada'
    expected = "(((x = 3) and y) > 'wada wada')"
    assert expected == term.eval()


def test_tree_with_params():
    term = (var('x') == qmark_param()) & (var('y') > 2) \
        & (var('z') <= qmark_param())
    expected = "(((x = ?) and (y > 2)) and (z <= ?))"
    assert expected == term.eval()


def test_tree_with_negation():
    term = (var('x') == qmark_param()) & ~(var('y') > 2) \
        & (var('z') <= qmark_param())
    expected = "(((x = ?) and not (y > 2)) and (z <= ?))"
    assert expected == term.eval()
