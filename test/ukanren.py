import os.path
import sys
import unittest
from microkanren.ukanren import *
from microkanren.macro import macros, conj, disj, goal, call

empty_state = State()

one_value = State({LVar(0):'hi'})
two_values = State({LVar(0):'hi', LVar(1):'bye'})
value_reference = State({LVar(0):LVar(1), LVar(1):'bye'})
identical_values = State({LVar(0):'hi', LVar(1):'hi'})

class Test_LVar(unittest.TestCase):
    def test_increment_id(self):
        oldId = LVar.nextId
        newVar = LVar()
        newId = LVar.nextId
        self.assertEqual(oldId, newVar.id)
        self.assertEqual(oldId + 1, newId)

    def test_var_without_name(self):
        oldId = LVar.nextId
        newVar = LVar()
        self.assertIsNone(newVar.name)
        self.assertEqual(newVar.id, oldId)

    def test_var_with_name(self):
        oldId = LVar.nextId
        newVar = LVar("test_name")
        self.assertEqual(newVar.name, "test_name")
        self.assertEqual(newVar.id, oldId)

    def test_vars_only_equal_if_id_equal(self):
        newVar1 = LVar("test_name")
        newVar2 = LVar("test_name")
        self.assertNotEqual(newVar1, newVar2)


class Test_State(unittest.TestCase):
    def test_valid_empty(self):
        newState = State()
        self.assertEqual(newState.substitution, {})
        self.assertTrue(newState.valid)

    def test_valid_with_sub(self):
        var = LVar()
        newState = State({var: 3})
        self.assertEqual(newState.substitution, {var: 3})
        self.assertTrue(newState.valid)

    def test_invalid(self):
        newState = State(valid=False)
        self.assertFalse(newState.valid)

class Test_Eq(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()

    def test_tautology(self):
        result = list(Eq(3,3).run())
        self.assertEqual(result, [State()])

    def test_not_eq(self):
        result = list(Eq(3,4).run())
        self.assertEqual(result, [])

    def varOnLeft(self):
        result = list(Eq(cls.var1, 3))

class Test_Conj(unittest.TestCase):
    def test_just_one_valid(self):
        result = list(Conj(Eq(3,3)).run())
        self.assertEqual(result, [State()])

    def test_just_one_invalid(self):
        result = list(Conj(Eq(2,3)).run())
        self.assertEqual(result, [])

class Test_Disj(unittest.TestCase):
    def test_just_one_valid(self):
        result = list(Disj(Eq(3,3)).run())
        self.assertEqual(result, [State()])

    def test_just_one_invalid(self):
        result = list(Disj(Eq(2,3)).run())
        self.assertEqual(result, [])

class Test_Fresh(unittest.TestCase):
    def test_empty_fresh(self):
        result = list(Fresh(lambda: Eq(3,3)).run())
        self.assertEqual(result, [State()])

    def test_one_fresh(self):
        result = list(Fresh(lambda x: Eq(x,3)).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].substitution), 1)
        var = list(result[0].substitution.keys())[0]
        self.assertEqual(var.name, 'x')

class Test_Call(unittest.TestCase):
    def test_empty_call(self):
        result = list(Fresh(lambda: Eq(3,3)).run())
        self.assertEqual(result, [State()])


if __name__ == "__main__":
    print("This test suite depends on macros to execute, so can't be")
    print("run independently. Please either run it through `run_tests.py`")
    print("above, or by importing it in a separate file.")
