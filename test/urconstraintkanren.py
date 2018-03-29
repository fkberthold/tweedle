import os.path
import sys
import unittest
from microkanren.urconstraintkanren import *

class Test_Link_Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.caucus_racers = Link("Dodo", Link("Mouse", Link("Duck")))
        cls.tea_partiers = Link("Hatter", Link("March Hare", Link("Dormouse")))

class Test_Link(Test_Link_Fixtures):
    def test_empty(self):
        result = Link()
        self.assertEqual(result, listToLinks([]))
        self.assertEqual(str(result), "()")

    def test_multiple_list(self):
        from_list = listToLinks(["Dodo", "Mouse", "Duck"])
        self.assertEqual(self.caucus_racers, from_list)
        self.assertEqual(str(self.caucus_racers), "('Dodo' 'Mouse' 'Duck')")

    def test_links_are_different(self):
        self.assertFalse(self.caucus_racers == self.tea_partiers)

    def test_is_in(self):
        self.assertTrue('Mouse' in self.caucus_racers)

    def test_is_not_in(self):
        self.assertFalse('Cheshire' in self.caucus_racers)

    def test_dotted_list(self):
        a_pair = Link("queen", "king")
        self.assertTrue(a_pair == a_pair)
        self.assertEqual(str(a_pair), "('queen' . 'king')")

    def test_nested_list(self):
        nested_expected = Link(self.caucus_racers)
        nested_result = listToLinks([["Dodo", "Mouse", "Duck"]])

class Test_LogicVariable_Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.breakfast = LogicVariable(7, "impossible")

class Test_LogicVariable(Test_LogicVariable_Fixtures):
    def test_has_name_display(self):
        self.assertEqual(self.breakfast.name, 'impossible')
        self.assertEqual(self.breakfast.id, 7)
        self.assertEqual(str(self.breakfast), "var(7, 'impossible')")

    def test_no_name_display(self):
        lvar = LogicVariable(7)
        self.assertEqual(lvar.name, None)
        self.assertEqual(lvar.id, 7)
        self.assertEqual(str(lvar), "var(7)")

    def test_equality(self):
        lvar1 = LogicVariable(2)
        lvar2 = var(2)
        dictVal = {lvar1:'three'}
        self.assertEqual(lvar1, lvar2)
        self.assertEqual(dictVal[lvar2], 'three')
        self.assertTrue(vareq(lvar1, lvar2))

    def test_not_equals(self):
        lvar1 = LogicVariable(2)
        lvar2 = LogicVariable(3)
        self.assertNotEqual(lvar1, lvar2)
        self.assertFalse(vareq(lvar1, lvar2))

    def test_is_variable(self):
        self.assertTrue(varq(self.breakfast))

    def test_is_not_variable(self):
        self.assertFalse(varq(7))

class Test_State_Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.empty = State()
        cls.just_alice = State({"eq": {(var(0), 'Alice')}}, 1)
        cls.with_one = State({"eq": {(var(0), 'Dum')}}, 1)
        cls.with_two = State({"eq": {(var(0), 'Dum'), (var(1), 'Dee')}}, 2)
        cls.with_linked = State({"eq": {(var(0), 'Queen'), (var(1), var(0))}}, 2)

class Test_State(Test_State_Fixtures):
    def test_empty_state_is_empty(self):
        self.assertEqual(self.empty, self.empty)
        self.assertEqual(self.empty.constraints, {})
        self.assertEqual(self.empty.count, 0)
        self.assertEqual(str(self.empty), "\nCount: 0\nConstraints:\n")

    def test_not_empty_state(self):
        self.assertEqual(self.with_one, self.with_one)
        self.assertEqual(self.with_one.constraints, {"eq":{(var(0), 'Dum')}})
        self.assertEqual(self.with_one.count, 1)
        self.assertEqual(str(self.with_one), "\nCount: 1\nConstraints:\n\teq:\n\t\t(var(0), 'Dum')\n")

    def test_walk_not_logic(self):
        result = walk('Dinah', self.with_one.constraints["eq"])
        self.assertEqual(result, 'Dinah')

    def test_different_states_differ(self):
        self.assertNotEqual(self.just_alice, self.with_one)

    def test_walk_one_level(self):
        result = walk(var(0), self.with_one.constraints["eq"])
        self.assertEqual(result, 'Dum')

    def test_walk_two_levels(self):
        result = walk(var(1), self.with_linked.constraints["eq"])
        self.assertEqual(result, 'Queen')

    def test_walk_var_missing(self):
        result = walk(var(1), self.with_one.constraints["eq"])
        self.assertEqual(result, var(1))

    def test_extend_substitution(self):
        substitution_with_dee = ext_s(var(1), 'Dee', self.with_one.constraints["eq"])
        state_with_dee = State({"eq":substitution_with_dee}, 2)
        self.assertEqual(state_with_dee, self.with_two)

    def test_zero_is_none(self):
        self.assertEqual(list(mzero), [])

    def test_unit_returns_state(self):
        self.assertEqual(list(unit(self.just_alice)), [self.just_alice])


class Test_Eq(Test_State_Fixtures):
    def test_eq_constants(self):
        new_states = list(eq(3, 3)(self.just_alice))
        print(new_states)
        self.assertEqual(len(new_states), 1)
        self.assertEqual(new_states[0], self.just_alice)

    def test_uneq_constants(self):
        new_states = list(eq(2, 3)(self.just_alice))
        self.assertEqual(len(new_states), 0)



if __name__ == "__main__":
    print("This test suite depends on macros to execute, so can't be")
    print("run independently. Please either run it through `run_tests.py`")
    print("above, or by importing it in a separate file.")

