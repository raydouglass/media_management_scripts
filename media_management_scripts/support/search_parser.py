from pyparsing import *
from functools import total_ordering

ParserElement.enablePackrat()


def resolve_from_context(context, path):
    d = context
    for key in path.split("."):
        if key in d:
            d = d[key]
        else:
            return None
    return d


class Operation:
    def __init__(self, s, l, t):
        self.s = s
        self.l = l
        self.t = t

    def exec(self, context):
        return self._exec(context)

    def resolve(self, context, var_name):
        if issubclass(type(var_name), Operation):
            return var_name.exec(context)
        elif type(var_name) == str:
            r = resolve_from_context(context, var_name)
            if r:
                return Variable(r)
        return var_name

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "{}<{} {} {}>".format(
            self.__class__.__name__, self.t[0][1], self.t[0][1], self.t[0][2]
        )


class GenericOperation(Operation):
    def _exec(self, context):
        return self.resolve(context, self.t[0])

    def __repr__(self):
        return "GenericOperation<{}>".format(self.t[0])


class TwoOperandOperation(Operation):
    def _exec(self, context):
        left = self.resolve(context, self.t[0][0])
        right = self.resolve(context, self.t[0][2])
        # print('Op={}, left={}, right={}'.format(self, left, right))
        return self._exec_two_operand(left, right)


class OneOperandOperation(Operation):
    def _exec(self, context):
        op = self.resolve(context, self.t[0][1])
        return self._exec_one_operand(op)

    def __repr__(self):
        return "{}<{} {}>".format(self.__class__, self.t[0][0], self.t[0][1])


class ComparisonOperation(Operation):
    def _exec(self, context):
        l = self.resolve(context, self.t[0][0])
        r = self.resolve(context, self.t[0][2])
        cmp = self.t[0][1]
        if cmp == "=":
            return l == r
        elif cmp == "!=":
            return l != r
        elif cmp == ">":
            return l > r
        elif cmp == ">=":
            return l >= r
        elif cmp == "<":
            return l < r
        elif cmp == "<=":
            return l <= r
        else:
            raise Exception()

    def __repr__(self):
        return "ComparisonOperation<{} {} {}>".format(
            self.t[0][0], self.t[0][1], self.t[0][2]
        )


class Addition(TwoOperandOperation):
    def _exec_two_operand(self, left, right):
        return left + right


class Subtraction(TwoOperandOperation):
    def _exec_two_operand(self, left, right):
        return left - right


class Multiplication(TwoOperandOperation):
    def _exec_two_operand(self, left, right):
        return left * right


class Division(TwoOperandOperation):
    def _exec_two_operand(self, left, right):
        return left / right


class And(TwoOperandOperation):
    def _exec_two_operand(self, left, right):
        return left and right


class Or(TwoOperandOperation):
    def _exec_two_operand(self, left, right):
        return left or right


class InOperation(TwoOperandOperation):
    def _exec_two_operand(self, left, right):
        # print('InOp: {} in {}'.format(left, right))
        return left in right


class Not(OneOperandOperation):
    def _exec_one_operand(self, op):
        return not op


class Negative(OneOperandOperation):
    def _exec_one_operand(self, op):
        return -op


class ListOperation(Operation):
    def _exec(self, context):
        return [self.resolve(context, x) for x in self.t[1]]


class IsNullOperation(Operation):
    def _exec(self, context):
        var_name = self.t[2]
        if issubclass(type(var_name), Operation):
            return var_name.exec(context)
        elif type(var_name) == str:
            d = context
            for key in var_name.split("."):
                if key in d:
                    d = d[key]
        return d is None

    def __repr__(self):
        return "IsNullOperation<{}>".format(self.t[2])


class AllOperation(Operation):
    def _exec(self, context):
        self.value = self.resolve(context, self.t[2])
        if issubclass(type(self.value), Variable):
            self.value = self.value.value
        return self

    def __eq__(self, other):
        if type(self.value) == list:
            for i in self.value:
                if i != other:
                    return False
            return True
        else:
            return self.value == other

    def __repr__(self):
        return "AllOperation<{}>".format(self.t[2])


@total_ordering
class Variable:
    def __init__(self, value):
        self.value = value
        self.all = all

    def __eq__(self, other):
        # print('Variable __eq__: self.value={}, all={}, other={}'.format(self.value, self.all, other))
        if type(self.value) == list:
            for i in self.value:
                if i == other:
                    return True
            return False
        else:
            return self.value == other

    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    def __mul__(self, other):
        return self.value * other

    def __truediv__(self, other):
        return self.value / other

    def __gt__(self, other):
        if type(self.value) == list:
            for i in self.value:
                if i > other:
                    return True
            return False
        else:
            return self.value > other

    def __repr__(self):
        return "Variable<value={}>".format(self.value)

    def __str__(self):
        return self.__repr__()


integer = Word(nums).setParseAction(lambda t: int(t[0]))
variable = Word(alphanums + "_")
dot_variable = delimitedList(variable, delim=".", combine=True)
string_var = QuotedString('"')

list_expr = (
    Literal("[")
    + Group(delimitedList(integer | variable | string_var, delim=",", combine=False))
    + Literal("]")
)
list_expr.setParseAction(ListOperation)

true_false = oneOf("true false", caseless=True).setParseAction(
    lambda s, l, t: t[0].lower() == "true"
)
none_op = (
    Literal("isNull") + Literal("(") + dot_variable + Literal(")")
).setParseAction(IsNullOperation)

all_op = (Literal("all") + Literal("(") + dot_variable + Literal(")")).setParseAction(
    AllOperation
)

operand = (
    true_false | none_op | integer | all_op | dot_variable | list_expr | string_var
)

andop = CaselessKeyword("and")
orop = CaselessKeyword("or")
notop = CaselessKeyword("not")
inop = CaselessKeyword("in")

expr = infixNotation(
    operand,
    [
        ("-", 1, opAssoc.RIGHT, Negative),
        ("*", 2, opAssoc.LEFT, Multiplication),
        ("/", 2, opAssoc.LEFT, Division),
        ("+", 2, opAssoc.LEFT, Addition),
        ("-", 2, opAssoc.LEFT, Subtraction),
        (oneOf("= != > >= < <="), 2, opAssoc.LEFT, ComparisonOperation),
        (inop, 2, opAssoc.LEFT, InOperation),
        (notop, 1, opAssoc.RIGHT, Not),
        (andop, 2, opAssoc.LEFT, And),
        (orop, 2, opAssoc.LEFT, Or),
    ],
).setParseAction(GenericOperation)


def parse(query: str) -> Operation:
    return expr.parseString(query, parseAll=True)[0]


def parse_and_execute(query: str, context: dict):
    return parse(query).exec(context)
