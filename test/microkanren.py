import os.path
import sys
import unittest
from microkanren.urkanren import *

empty_state = State()

one_value = State({var(0):'hi'}, 1)
two_values = State({var(0):'hi', var(1):'bye'}, 2)
value_reference = State({var(0):var(1), var(1):'bye'}, 2)
identical_values = State({var(0):'hi', var(1):'hi'}, 2)

class Test_CoreMicroKanren(unittest.TestCase):
    def test_base_var(self):
        self.assertTrue(var(1).id == LogicVariable(1).id)

    def test_base_varq(self):
        self.assertTrue(varq(var(1)))

    def test_neg_varq(self):
        self.assertFalse(varq(1))

    def test_base_vareq(self):
        self.assertTrue(vareq(var(1), var(1)))

    def test_base_vareq(self):
        self.assertFalse(vareq(var(1), var(2)))

    def test_base_case_walk(self):
        self.assertEqual(walk(1, one_value.substitution), 1)

    def test_variable_case_walk(self):
        self.assertEqual(walk(var(0), two_values.substitution), 'hi')

    def test_reference_walk(self):
        self.assertEqual(walk(var(0), value_reference.substitution), 'bye')

    def test_base_ext_s(self):
        self.assertCountEqual(ext_s(var(1), 'bye', one_value.substitution), two_values.substitution)

    def test_literal_eq(self):
        self.assertCountEqual(eq(1, 1)(one_value), [one_value])

    def test_literal_not_eq(self):
        self.assertCountEqual(eq(1, 2)(one_value), [])

    def test_literal_var_eq(self):
        self.assertCountEqual(eq(var(0), 'hi')(one_value), [one_value])

    def test_list_eq(self):
        self.assertCountEqual(call_fresh(lambda f:eq([1,2], [1,f]))(empty_state), [State({var(0):2}, 1)])

    def test_unify_base(self):
        self.assertCountEqual(unify(var(0), var(1), identical_values.substitution), identical_values.substitution)

    def test_unify_not_base(self):
        self.assertFalse(unify(var(0), var(1), two_values.substitution))

    def test_call_fresh_base(self):
        self.assertCountEqual(((list(call_fresh(lambda g: eq(g, var(0)))(two_values)))[0].substitution), {**two_values.substitution, **{var(2): 'hi'}})

    def test_call_fresh_nest(self):
        call = (lambda f: call_fresh(lambda g: eq(f, g)))
        self.assertCountEqual(call_fresh(call)(empty_state), [State({var(0):var(1)},2)])

    def test_disj_base(self):
        call = (lambda f: disj(eq(f, var(0)), eq(f, var(1))))
        choice1 = State({**{var(2):'hi'}, **(two_values.substitution)}, 3)
        choice2 = State({**{var(2):'bye'}, **(two_values.substitution)}, 3)
        self.assertCountEqual(list(call_fresh(call)(two_values)), [choice1, choice2])

    def test_disj_several(self):
        call = (lambda f, g: disj(eq(f, var(0)), eq(f, var(1)), eq(g, var(0))))
        choice1 = State({**{var(2):'hi'}, **(two_values.substitution)}, 4)
        choice2 = State({**{var(2):'bye'}, **(two_values.substitution)}, 4)
        choice3 = State({**{var(3):'hi'}, **(two_values.substitution)}, 4)
        self.assertCountEqual(list(call_fresh(call)(two_values)), [choice1, choice2, choice3])

    def test_conj_base(self):
        call = lambda f, g: conj(eq(f, g), eq(g, var(0)))
        choice = State({**{var(3):'hi', var(2):var(3)}, **(two_values.substitution)}, 4)
        self.assertCountEqual(list(call_fresh(call)(two_values)), [choice])

    def test_conj_several(self):
        call = lambda f, g, h: conj(eq(f, g), eq(g, var(0)), eq(h, var(1)))
        choice = State({**{var(3):'hi', var(2):var(3), var(4):'bye'}, **(two_values.substitution)}, 5)
        self.assertCountEqual(list(call_fresh(call)(two_values)), [choice])

if __name__ == "__main__":
    unittest.main()
