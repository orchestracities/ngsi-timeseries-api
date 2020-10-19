# TODO: replace code below w/ decent AST lib when you find one.


class Term:

    def eval(self) -> str:
        pass
# NOTE. Performance.
# This signature sort of lends itself to possibly inefficient string
# concatenation where the parent node evaluates the children folding
# '+' in between: eval(c1) + eval(c2) + ... + eval(cn)
# We should concoct a better eval strategy, e.g. passing in a stream...

    @staticmethod
    def to_term(x):
        return x if isinstance(x, Term) else LitTerm(x)

    def __and__(self, other):
        return BinOp(self, 'and', self.to_term(other))

    def __or__(self, other):
        return BinOp(self, 'or', self.to_term(other))

    def __eq__(self, other):
        return BinOp(self, '=', self.to_term(other))

    def __ne__(self, other):
        return BinOp(self, '<>', self.to_term(other))

    def __lt__(self, other):
        return BinOp(self, '<', self.to_term(other))

    def __le__(self, other):
        return BinOp(self, '<=', self.to_term(other))

    def __gt__(self, other):
        return BinOp(self, '>', self.to_term(other))

    def __ge__(self, other):
        return BinOp(self, '>=', self.to_term(other))

    def __invert__(self):
        return UnaryOp('not', self)

# NOTE. Typing.
# Or lack thereof! Combining terms this way doesn't prevent you from shooting
# yourself in the foot, as in: ('wot?!' and (x < true))


class UnaryOp(Term):

    def __init__(self, operator: str, rhs: Term):
        self.operator = operator
        self.rhs = rhs

    def eval(self):
        return '{} {}'.format(self.operator,
                              self.rhs.eval())


class BinOp(Term):

    def __init__(self, lhs: Term, operator: str, rhs: Term):
        self.operator = operator
        self.lhs = lhs
        self.rhs = rhs

    def eval(self):
        return '({} {} {})'.format(self.lhs.eval(),
                                   self.operator,
                                   self.rhs.eval())


class LitTerm(Term):

    def __init__(self, value, to_str=str, quote="'"):
        self.value = value
        self.converter = to_str
        self.quote = quote

    def eval(self):
        str_rep = 'null' if self.value is None else self.converter(self.value)
        if isinstance(self.value, str):
            str_rep = '{}{}{}'.format(self.quote, str_rep, self.quote)
        return str_rep
# NOTE. SQL Injection.
# The above quoting isn't enough to prevent attacks---e.g. read through
# https://stackoverflow.com/questions/139199 or google "sql injection escape
# characters bypass", "avoid sql injection by quoting sql string", etc.
# It's the converter's job to make sure the string is safe.


def var(v: str):
    return LitTerm(value=v, quote='')


def lit(v):
    return LitTerm(v)


def qmark_param():
    return LitTerm(value='?', quote='')


def numeric_param(index: int):
    v = ':{}'.format(index)
    return LitTerm(value=v, quote='')


def named_param(name: str):
    v = ':{}'.format(name)
    return LitTerm(value=v, quote='')


def pyformat_param(name: str):
    v = '%({})s'.format(name)
    return LitTerm(value=v, quote='')
