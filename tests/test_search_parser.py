import unittest
from pyparsing import ParseException

from media_management_scripts.support.search_parser import parse_and_execute, parse


class ParseTestCase:
    def parse(self, query, expected, context={}):
        self.assertEqual(parse_and_execute(query, context), expected)


class SimpleTest(unittest.TestCase, ParseTestCase):
    def test_basic(self):
        self.parse("1+1", 2)
        self.parse("1-1", 0)
        self.parse("-1-2", -3)
        self.parse("3*2", 6)
        self.parse("10/2", 5)

    def test_whitespace(self):
        self.parse(" 1 + 1 ", 2)
        self.parse(" 1      + 1 ", 2)

    def test_order_of_operations(self):
        self.parse("1+2*3", 7)
        self.parse("2*3+1", 7)
        self.parse("(1+2)*3", 9)

    def test_boolean(self):
        self.parse("true", True)
        self.parse("false", False)
        self.parse("true and true", True)
        self.parse("true and false", False)
        self.parse("True and False", False)
        self.parse("true or false", True)
        self.parse("not true", False)
        self.parse("not false", True)

    def test_boolean_order_of_operations(self):
        self.parse("true and true or false", True)
        self.parse("not false and false", False)
        self.parse("not false or false", True)
        self.parse("1 in [1] or false", True)
        self.parse("1 in [1] and false", False)

    def test_comparison(self):
        self.parse("1 = 1", True)
        self.parse("1 != 1", False)
        self.parse("1 != 2", True)
        self.parse("1 > 1", False)
        self.parse("2 > 1", True)
        self.parse("1 < 1", False)
        self.parse("1 >= 1", True)
        self.parse("1 <= 1", True)

    def test_in(self):
        self.parse("1 in [1]", True)
        self.parse("1 in [1,2]", True)
        self.parse("2 in [1]", False)

    def test_basic_context(self):
        self.parse("a", 2, {"a": 2})
        self.parse("a+1", 3, {"a": 2})
        self.parse("a.b+1", 3, {"a": {"b": 2}})

    def test_reuse(self):
        op = parse("a+1")
        self.assertEqual(2, op.exec({"a": 1}))
        self.assertEqual(3, op.exec({"a": 2}))

    def test_invalid(self):
        with self.assertRaises(ParseException):
            parse("True and")
        with self.assertRaises(ParseException):
            parse("1+")

    def test_isNull(self):
        self.parse("isNull(1)", False)
        self.parse("isNull(a)", True, {"a": None})
        self.parse("not isNull(a)", True, {"a": 1})

    def test_all(self):
        self.parse("a = 1", True, {"a": [1, 2]})
        self.parse("all(a) = 1", True, {"a": [1, 1]})
        self.parse("all(a) = 1", False, {"a": [1, 2]})
        self.parse("all(a) != 1", True, {"a": [1, 2]})
        self.parse("all(a) != 1", False, {"a": [1, 1]})

    def test_string(self):
        self.parse('"test"', "test")
        self.parse("test", "test")
        self.parse('"test test"', "test test")
        self.parse('"test  test"', "test  test")
        self.parse('"test test" = "test test"', True)
