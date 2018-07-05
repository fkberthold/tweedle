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
def isTeaOrCake(x):
    with disj:
        Eq(x, 'tea')
        Eq(x, 'cake')

class Test_Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()
        cls.dinner_party = ['The Walrus', 'The Carpenter']
        cls.tea_party = ['Mad Hatter', 'March Hare', 'The Dormouse']
        cls.combatants = {'Dee', 'Dum', 'Raven'}
        cls.changes = {'drink me':'smaller', 'eat me':'bigger'}

class Test_LVar(Test_Fixtures):
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
        newVar = LVar("White Rabbit")
        self.assertEqual(newVar.name, "White Rabbit")
        self.assertEqual(newVar.id, oldId)
        self.assertEqual(str(newVar), "%s(%i)" % (newVar.name, newVar.id))

    def test_vars_only_equal_if_id_equal(self):
        newVar1 = LVar("Red Rose")
        newVar2 = LVar("White Rose")
        self.assertNotEqual(newVar1, newVar2)

class Test_State(Test_Fixtures):
    def test_valid_empty(self):
        newState = State()
        self.assertEqual(newState.substitution, {})
        self.assertTrue(newState.valid)
        self.assertEqual(len(newState), 0)
        self.assertEqual(str(newState), "Substitutions:\n")

    def test_valid_with_sub(self):
        var = LVar()
        newState = State({var: "Alice"})
        self.assertEqual(newState.substitution, {var: "Alice"})
        self.assertTrue(newState.valid)
        self.assertEqual(len(newState), 1)
        self.assertEqual(str(newState), "Substitutions:\n  %s: %s\n" % (str(var), "'Alice'"))

    def test_invalid(self):
        newState = State(valid=False)
        self.assertFalse(newState.valid)
        self.assertEqual(str(newState), "State Invalid")

class Test_Fail(Test_Fixtures):
    def test_valid_state_fails(self):
        newState = State()
        result = list(Fail().run(newState))
        self.assertEqual(result, [])

    def test_invalid_state_fails(self):
        newState = State(valid=False)
        result = list(Fail().run(newState))
        self.assertEqual(result, [])

class Test_Succeed(Test_Fixtures):
    def test_valid_state_succeeds(self):
        newState = State()
        result = list(Succeed().run(newState))
        self.assertEqual(result, [newState])

    def test_invalid_state_fails(self):
        newState = State(valid=False)
        result = list(Succeed().run(newState))
        self.assertEqual(result, [])


class Test_Eq(Test_Fixtures):
    def test_repr(self):
        result = Eq('Roses','Roses')
        self.assertEqual(str(result), "Eq('Roses','Roses')")

    def test_tautology(self):
        result = list(Eq(0,0).run())
        self.assertEqual(result, [State()])

    def test_same_variable(self):
        result = list(Eq(self.var1, self.var1).run())
        self.assertEqual(result, [State()])

    def test_not_eq(self):
        result = list(Eq('Red Roses','White Roses').run())
        self.assertEqual(result, [])

    def test_var_on_left(self):
        result = list(Eq(self.var1, 'Roses').run())
        self.assertEqual(result[0][self.var1], 'Roses')

    def test_var_on_right(self):
        result = list(Eq('Roses', self.var1).run())
        self.assertEqual(result[0][self.var1], 'Roses')

    def test_var_on_both(self):
        result = list(Eq(self.var1, self.var2).run())
        self.assertEqual(result[0][self.var1], self.var2)

    def test_is_list(self):
        result = list(Eq(self.var1, self.tea_party).run())
        self.assertEqual(result[0][self.var1], self.tea_party)

    def test_in_list_head(self):
        result = list(Eq([self.var1, 'March Hare', 'The Dormouse'], self.tea_party).run())
        self.assertEqual(result[0][self.var1], 'Mad Hatter')

    def test_in_list_tail(self):
        result = list(Eq(['Mad Hatter', self.var1, 'The Dormouse'], self.tea_party).run())
        self.assertEqual(result[0][self.var1], 'March Hare')

    def test_is_dictionary(self):
        result = list(Eq(self.var1, self.changes).run())
        self.assertEqual(result[0][self.var1], self.changes)

    def test_is_dictionary_key(self):
        result = list(Eq({self.var1:'smaller', 'eat me':'bigger'}, self.changes).run())
        self.assertEqual(result[0][self.var1], 'drink me')

    def test_is_dictionary_value(self):
        result = list(Eq({'drink me':self.var1, 'eat me':'bigger'}, self.changes).run())
        self.assertEqual(result[0][self.var1], 'smaller')

    def test_is_dictionary_ambiguous_key(self):
        result = list(Eq({self.var1:'what', self.var2:'what'}, {'I eat':'what', 'I see':'what'}).run())
        self.assertEqual(len(result), 2)
        self.assertIn(State({self.var1:'I eat', self.var2:'I see'}), result)
        self.assertIn(State({self.var1:'I see', self.var2:'I eat'}), result)

    def test_is_set(self):
        result = list(Eq(self.var1, self.combatants).run())
        self.assertEqual(result[0][self.var1], self.combatants)

    def test_in_set(self):
        result = list(Eq({'Dee', self.var1, 'Dum'}, self.combatants).run())
        self.assertEqual(result[0][self.var1], 'Raven')

    def test_is_set_ambiguous(self):
        result = list(Eq({self.var1, self.var2}, {'Dee', 'Dum'}).run())
        self.assertEqual(len(result), 2)
        self.assertIn(State({self.var1:'Dee', self.var2:'Dum'}), result)
        self.assertIn(State({self.var1:'Dum', self.var2:'Dee'}), result)

class Test_Conj(Test_Fixtures):
    def test_empty(self):
        goal = Conj()
        result = list(goal.run())

        self.assertEqual(str(goal), "EMPTY CONJ")
        self.assertEqual(result, [State()])

    def test_just_one_valid(self):
        result = list(Conj(Eq('Alice','Alice')).run())
        self.assertEqual(result, [State()])

    def test_just_one_invalid(self):
        result = list(Conj(Eq('Alice','Dinah')).run())
        self.assertEqual(result, [])

    def test_two_without_branching(self):
        with conj(traveller), conj as testConj:
            Eq(traveller, self.var1)
            Eq(traveller, 'Alice')

        result = list(testConj.run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 'Alice')

    def test_two_amper_to_string(self):
        testConj = Eq(self.var1, 'Alice') & Eq(self.var2, 'Dinah')

        self.assertEqual(str(testConj), "Eq(%s,'Alice') & Eq(%s,'Dinah')" % (str(self.var1), str(self.var2)))

    def test_two_amper_without_branching(self):
        testConj = Fresh(lambda cat: Eq(cat, self.var1) & Eq(cat, 'Cheshire'))

        result = list(testConj.run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 'Cheshire')

    def test_two_with_branching(self):
        with conj(rattle, dum), conj as testConj:
            with disj:
                Eq(rattle, 'spoiled')
                Eq(rattle, 'spoilt')
            Eq(rattle, self.var2)
            Eq(dum, 'angry')
            Eq(dum, self.var1)

        result = list(testConj.run())
        self.assertEqual(len(result), 2)
        for r in result:
            self.assertEqual(r[self.var1], 'angry')
        isSpoiled = [st for st in result if st[self.var2] == 'spoiled']
        isSpoilt = [st for st in result if st[self.var2] == 'spoilt']
        self.assertEqual(len(isSpoiled), 1)
        self.assertEqual(len(isSpoilt), 1)

class Test_Disj(Test_Fixtures):
    def test_empty(self):
        goal = Disj()
        result = list(goal.run())

        self.assertEqual(str(goal), "EMPTY DISJ")
        self.assertEqual(result, [])

    def test_just_one_valid(self):
        result = list(Disj(Eq('Queen','Queen')).run())
        self.assertEqual(result, [State()])

    def test_just_one_invalid(self):
        result = list(Disj(Eq('Pawn','Queen')).run())
        self.assertEqual(result, [])

    def test_two(self):
        with disj as testDisj:
            Eq(self.var1, 'Walrus')
            Eq(self.var1, 'Carpenter')

        result = list(testDisj.run())
        self.assertEqual(len(result), 2)
        hasWalrus = [st for st in result if st[self.var1] == 'Walrus']
        hasCarpenter = [st for st in result if st[self.var1] == 'Carpenter']
        self.assertEqual(len(hasWalrus), 1)
        self.assertEqual(len(hasCarpenter), 1)

    def test_two_operator(self):
        testDisj = (Eq(self.var1, 'Walrus') | Eq(self.var1, 'Carpenter'))
        self.assertEqual(str(testDisj), "Eq(%s,'Walrus') | Eq(%s,'Carpenter')" % (str(self.var1), str(self.var1)))

        result = list(testDisj.run())
        self.assertEqual(len(result), 2)
        has3 = [st for st in result if st[self.var1] == 'Walrus']
        has4 = [st for st in result if st[self.var1] == 'Carpenter']
        self.assertEqual(len(has3), 1)
        self.assertEqual(len(has4), 1)

    def test_get_first(self):
        with disj as testDisj:
            Eq(self.var1, 'Walrus')
            Eq(self.var1, 'Carpenter')

        result = list(testDisj.run(results=1))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 'Walrus')

class Test_Fresh(Test_Fixtures):
    def test_empty_fresh(self):
        result = list(Fresh(lambda: Eq('King','King')).run())
        self.assertEqual(result, [State()])

    def test_one_fresh(self):
        next_var_id = LVar.nextId
        goal = Fresh(lambda x: Eq(x,'King'))
        self.assertEqual(str(goal), "Fresh [x(%i)]: <class 'microkanren.ukanren.Eq'>" % next_var_id)
        result = list(goal.run())
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].substitution), 1)
        var = list(result[0].substitution.keys())[0]
        self.assertEqual(var.name, 'x')

class Test_Call(Test_Fixtures):
    def test_empty_call(self):
        result = list(Call(lambda: Eq('Knight','Knight')).run())
        self.assertEqual(result, [State()])

    def test_call_block(self):
        with call(x), call as callTest:
            with disj:
                Eq(x, 'Treacle')
                Eq(x, 'Honey')
        result = list(callTest.run())
        self.assertEqual(len(result), 2)
        var = [key for key in result[0].substitution.keys() if key.name == 'x'][0]
        hasTreacle = [st for st in result if st[var] == 'Treacle']
        hasHoney = [st for st in result if st[var] == 'Honey']
        self.assertEqual(len(hasTreacle), 1)
        self.assertEqual(len(hasHoney), 1)

class Test_Goal(Test_Fixtures):
    def test_one_var(self):
        result = list(isTeaOrCake(self.var1).run())
        self.assertEqual(len(result), 2)
        hasTea = [st for st in result if st[self.var1] == 'tea']
        hasCake = [st for st in result if st[self.var1] == 'cake']
        self.assertEqual(len(hasTea), 1)
        self.assertEqual(len(hasCake), 1)


if __name__ == "__main__":
    print("This test suite depends on macros to execute, so can't be")
    print("run independently. Please either run it through `run_tests.py`")
    print("above, or by importing it in a separate file.")
