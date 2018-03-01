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

@goal
def is3or4(x):
    with disj:
        Eq(x, 3)
        Eq(x, 4)

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
        self.assertEqual(str(newVar), "%i" % newVar.id)

    def test_var_with_name(self):
        oldId = LVar.nextId
        newVar = LVar("test_name")
        self.assertEqual(newVar.name, "test_name")
        self.assertEqual(newVar.id, oldId)
        self.assertEqual(str(newVar), "%s(%i)" % (newVar.name, newVar.id))

    def test_vars_only_equal_if_id_equal(self):
        newVar1 = LVar("test_name")
        newVar2 = LVar("test_name")
        self.assertNotEqual(newVar1, newVar2)

class Test_State(unittest.TestCase):
    def test_valid_empty(self):
        newState = State()
        self.assertEqual(newState.substitution, {})
        self.assertTrue(newState.valid)
        self.assertEqual(len(newState), 0)
        self.assertEqual(str(newState), "Substitutions:\n")

    def test_valid_with_sub(self):
        var = LVar()
        newState = State({var: 3})
        self.assertEqual(newState.substitution, {var: 3})
        self.assertTrue(newState.valid)
        self.assertEqual(len(newState), 1)
        self.assertEqual(str(newState), "Substitutions:\n  %s: %s\n" % (str(var), 3))

    def test_invalid(self):
        newState = State(valid=False)
        self.assertFalse(newState.valid)
        self.assertEqual(str(newState), "State Invalid")

class Test_Fail(unittest.TestCase):
    def test_valid_state_fails(self):
        newState = State()
        result = list(Fail().run(newState))
        self.assertEqual(result, [])

    def test_invalid_state_fails(self):
        newState = State(valid=False)
        result = list(Fail().run(newState))
        self.assertEqual(result, [])

class Test_Succeed(unittest.TestCase):
    def test_valid_state_succeeds(self):
        newState = State()
        result = list(Succeed().run(newState))
        self.assertEqual(result, [newState])

    def test_invalid_state_fails(self):
        newState = State(valid=False)
        result = list(Succeed().run(newState))
        self.assertEqual(result, [])


class Test_Eq(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()

    def test_repr(self):
        result = Eq(3,3)
        self.assertEqual(str(result), "Eq(3,3)")

    def test_tautology(self):
        result = list(Eq(3,3).run())
        self.assertEqual(result, [State()])

    def test_same_variable(self):
        result = list(Eq(self.var1, self.var1).run())
        self.assertEqual(result, [State()])

    def test_not_eq(self):
        result = list(Eq(3,4).run())
        self.assertEqual(result, [])

    def test_var_on_left(self):
        result = list(Eq(self.var1, 3).run())
        self.assertEqual(result[0][self.var1], 3)

    def test_var_on_right(self):
        result = list(Eq(3, self.var1).run())
        self.assertEqual(result[0][self.var1], 3)

    def test_var_on_both(self):
        result = list(Eq(self.var1, self.var2).run())
        self.assertEqual(result[0][self.var1], self.var2)

    def test_is_string(self):
        result = list(Eq(self.var1, "Test String").run())
        self.assertEqual(result[0][self.var1], "Test String")

    def test_are_strings(self):
        result = list(Eq("Test String", "Test String").run())
        self.assertEqual(len(result), 1)

    def test_are_diff_strings(self):
        result = list(Eq("Test String 1", "Test String 2").run())
        self.assertEqual(len(result), 0)

    def test_is_list(self):
        result = list(Eq(self.var1, [1, 2, 3]).run())
        self.assertEqual(result[0][self.var1], [1, 2, 3])

    def test_in_list_head(self):
        result = list(Eq([self.var1, 2, 3], [1, 2, 3]).run())
        self.assertEqual(result[0][self.var1], 1)

    def test_in_list_tail(self):
        result = list(Eq([1, self.var1, 3], [1, 2, 3]).run())
        self.assertEqual(result[0][self.var1], 2)

    def test_is_dictionary(self):
        result = list(Eq(self.var1, {1:2, 3:4}).run())
        self.assertEqual(result[0][self.var1], {1:2, 3:4})

    def test_is_dictionary_key(self):
        result = list(Eq({self.var1:2, 3:4}, {1:2, 3:4}).run())
        self.assertEqual(result[0][self.var1], 1)

    def test_is_dictionary_value(self):
        result = list(Eq({1:self.var1, 3:4}, {1:2, 3:4}).run())
        self.assertEqual(result[0][self.var1], 2)

    def test_is_dictionary_ambiguous_key(self):
        result = list(Eq({self.var1:2, self.var2:2}, {1:2, 3:2}).run())
        self.assertEqual(len(result), 2)
        self.assertIn(State({self.var1:1, self.var2:3}), result)
        self.assertIn(State({self.var1:3, self.var2:1}), result)

    def test_is_set(self):
        result = list(Eq(self.var1, {1, 2, 3}).run())
        self.assertEqual(result[0][self.var1], {1, 2, 3})

    def test_in_set(self):
        result = list(Eq({1, self.var1, 3}, {1, 2, 3}).run())
        self.assertEqual(result[0][self.var1], 2)

    def test_is_set_ambiguous(self):
        result = list(Eq({self.var1, self.var2}, {1, 3}).run())
        self.assertEqual(len(result), 2)
        self.assertIn(State({self.var1:1, self.var2:3}), result)
        self.assertIn(State({self.var1:3, self.var2:1}), result)

class Test_Conj(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()

    def test_empty(self):
        goal = Conj()
        result = list(goal.run())

        self.assertEqual(str(goal), "EMPTY CONJ")
        self.assertEqual(result, [State()])

    def test_just_one_valid(self):
        result = list(Conj(Eq(3,3)).run())
        self.assertEqual(result, [State()])

    def test_just_one_invalid(self):
        result = list(Conj(Eq(2,3)).run())
        self.assertEqual(result, [])

    def test_two_without_branching(self):
        with conj(x), conj as testConj:
            Eq(x, self.var1)
            Eq(x, 3)

        result = list(testConj.run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 3)

    def test_two_amper_to_string(self):
        testConj = Eq(self.var1, 3) & Eq(self.var2, 4)

        self.assertEqual(str(testConj), "Eq(%s,3) & Eq(%s,4)" % (str(self.var1), str(self.var2)))

    def test_two_amper_without_branching(self):
        testConj = Fresh(lambda x: Eq(x, self.var1) & Eq(x, 3))

        result = list(testConj.run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 3)

    def test_two_with_branching(self):
        with conj(x, y), conj as testConj:
            with disj:
                Eq(y, 4)
                Eq(y, 5)
            Eq(y, self.var2)
            Eq(x, 3)
            Eq(x, self.var1)

        result = list(testConj.run())
        self.assertEqual(len(result), 2)
        for r in result:
            self.assertEqual(r[self.var1], 3)
        has4 = [st for st in result if st[self.var2] == 4]
        has5 = [st for st in result if st[self.var2] == 5]
        self.assertEqual(len(has4), 1)
        self.assertEqual(len(has5), 1)

class Test_Disj(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()

    def test_empty(self):
        goal = Disj()
        result = list(goal.run())

        self.assertEqual(str(goal), "EMPTY DISJ")
        self.assertEqual(result, [])

    def test_just_one_valid(self):
        result = list(Disj(Eq(3,3)).run())
        self.assertEqual(result, [State()])

    def test_just_one_invalid(self):
        result = list(Disj(Eq(2,3)).run())
        self.assertEqual(result, [])

    def test_two(self):
        with disj as testDisj:
            Eq(self.var1, 3)
            Eq(self.var1, 4)

        result = list(testDisj.run())
        self.assertEqual(len(result), 2)
        has3 = [st for st in result if st[self.var1] == 3]
        has4 = [st for st in result if st[self.var1] == 4]
        self.assertEqual(len(has3), 1)
        self.assertEqual(len(has4), 1)

    def test_two_operator(self):
        testDisj = (Eq(self.var1, 3) | Eq(self.var1, 4))
        self.assertEqual(str(testDisj), "Eq(%s,3) | Eq(%s,4)" % (str(self.var1), str(self.var1)))

        result = list(testDisj.run())
        self.assertEqual(len(result), 2)
        has3 = [st for st in result if st[self.var1] == 3]
        has4 = [st for st in result if st[self.var1] == 4]
        self.assertEqual(len(has3), 1)
        self.assertEqual(len(has4), 1)

    def test_get_first(self):
        with disj as testDisj:
            Eq(self.var1, 3)
            Eq(self.var1, 4)

        result = list(testDisj.run(results=1))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 3)

class Test_Fresh(unittest.TestCase):
    def test_empty_fresh(self):
        result = list(Fresh(lambda: Eq(3,3)).run())
        self.assertEqual(result, [State()])

    def test_one_fresh(self):
        next_var_id = LVar.nextId
        goal = Fresh(lambda x: Eq(x,3))
        self.assertEqual(str(goal), "Fresh [x(%i)]: <class 'microkanren.ukanren.Eq'>" % next_var_id)
        result = list(goal.run())
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].substitution), 1)
        var = list(result[0].substitution.keys())[0]
        self.assertEqual(var.name, 'x')

class Test_Call(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()

    def test_empty_call(self):
        result = list(Call(lambda: Eq(3,3)).run())
        self.assertEqual(result, [State()])

    def test_call_block(self):
        with call(x), call as callTest:
            with disj:
                Eq(x, 3)
                Eq(x, 4)
        result = list(callTest.run())
        self.assertEqual(len(result), 2)
        var = [key for key in result[0].substitution.keys() if key.name == 'x'][0]
        has3 = [st for st in result if st[var] == 3]
        has4 = [st for st in result if st[var] == 4]
        self.assertEqual(len(has3), 1)
        self.assertEqual(len(has4), 1)

class Test_Goal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()

    def test_one_var(self):
        result = list(is3or4(self.var1).run())
        self.assertEqual(len(result), 2)
        has3 = [st for st in result if st[self.var1] == 3]
        has4 = [st for st in result if st[self.var1] == 4]
        self.assertEqual(len(has3), 1)
        self.assertEqual(len(has4), 1)


if __name__ == "__main__":
    print("This test suite depends on macros to execute, so can't be")
    print("run independently. Please either run it through `run_tests.py`")
    print("above, or by importing it in a separate file.")
