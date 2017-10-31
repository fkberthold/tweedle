import os.path
import sys
import unittest
from ..microkanren.urkanren import *

empty_state = ([], 0)

one_value = ([([0], 'hi')], 1)
two_values = ([([0], 'hi'), ([1], 'bye')], 2)
value_reference = ([([0], [1]), ([1], 'bye')], 2)
identical_values = ([([0], 'hi'), ([1], 'hi')], 2)

class Test_CoreMicroKanren(unittest.TestCase):
    def test_base_var(self):
        self.assertEqual(var(1), [1])

    def test_base_varq(self):
        self.assertTrue(varq(var(1)))

    def test_neg_varq(self):
        self.assertFalse(varq(1))

    def test_base_vareq(self):
        self.assertTrue(vareq(var(1), var(1)))

    def test_base_vareq(self):
        self.assertFalse(vareq(var(1), var(2)))

    def test_base_case_walk(self):
        self.assertEqual(walk(1, one_value[0]), 1)

    def test_variable_case_walk(self):
        self.assertEqual(walk([0], two_values[0]), 'hi')

    def test_reference_walk(self):
        self.assertEqual(walk([0], value_reference[0]), 'bye')

    def test_base_ext_s(self):
        self.assertItemsEqual(ext_s(var(1), 'bye', one_value[0]), two_values[0])

    def test_literal_eq(self):
        self.assertItemsEqual(eq(1, 1)(one_value), [one_value])

    def test_literal_not_eq(self):
        self.assertEqual(eq(1, 2)(one_value), [])

    def test_literal_var_eq(self):
        self.assertItemsEqual(eq([0], 'hi')(one_value), [one_value])

if __name__ == "__main__":
    unittest.main()
