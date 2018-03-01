import os.path
import sys
import unittest
from microkanren.ukanren import *
from microkanren.collections import *
from microkanren.macro import macros, conj, disj, goal, call

class Test_List_Leno(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()

    def test_empty_0(self):
        result = list(list_leno([], 0).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_single_1(self):
        result = list(list_leno(['foo'], 1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_two_2(self):
        result = list(list_leno(['foo', 'bar'], 2).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_empty_x(self):
        result = list(list_leno([], self.var1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 0)

    def test_single_x(self):
        result = list(list_leno(['foo'], self.var1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 1)

    def test_two_x(self):
        result = list(list_leno(['foo', 'bar'], self.var1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 2)

    def test_x_0(self):
        result = list(list_leno(self.var1, 0).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], [])

    def test_x_1(self):
        result = list(list_leno(self.var1, 1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0][self.var1]), 1)
        self.assertTrue(all([varq(v) for v in result[0][self.var1]]))

    def test_x_2(self):
        result = list(list_leno(self.var1, 2).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0][self.var1]), 2)
        self.assertTrue(all([varq(v) for v in result[0][self.var1]]))

    def test_x_y(self):
        result = list(list_leno(self.var1, self.var2).run(results=3))
        self.assertEqual(len(result), 3)
        self.assertEqual(len(result[0][self.var1]), 0)
        self.assertEqual(len(result[1][self.var1]), 1)
        self.assertEqual(len(result[2][self.var1]), 2)
        self.assertTrue(all([varq(v) for st in result for v in st[self.var1]]))


class Test_Indexo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()

    def test_all_constant_succeeds(self):
        result = list(indexo([5, 6, 7], 5, 0).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_all_constant_succeeds_from_back(self):
        result = list(indexo([5, 6, 7], 7, -1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_all_constant_succeeds_on_first_duplicate(self):
        result = list(indexo([5, 6, 5], 5, 0).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_all_constant_succeeds_on_second_duplicate(self):
        result = list(indexo([5, 6, 5], 5, 2).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_all_constant_fails_out_of_bounds(self):
        result = list(indexo([5, 6, 7], 5, 3).run())
        self.assertEqual(len(result), 0)

    def test_all_constant_fails_wrong_value(self):
        result = list(indexo([5, 6, 7], 6, 0).run())
        self.assertEqual(len(result), 0)

if __name__ == "__main__":
    print("This test suite depends on macros to execute, so can't be")
    print("run independently. Please either run it through `run_tests.py`")
    print("above, or by importing it in a separate file.")
