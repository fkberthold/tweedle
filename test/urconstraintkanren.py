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
        self.assertEqual(result, list_to_links([]))
        self.assertEqual(str(result), "()")

    def test_multiple_list(self):
        from_list = list_to_links(["Dodo", "Mouse", "Duck"])
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
        nested_result = list_to_links([["Dodo", "Mouse", "Duck"]])

    def test_none_is_empty_link(self):
        self.assertTrue(None == Link())

    def test_empty_link_is_none(self):
        self.assertTrue(Link() == None)

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
        cls.alice_linked = State({"eq": {(var(0), 'Alice'), (var(1), var(0))}}, 2)
        cls.two_alices = State({"eq": {(var(0), 'Alice'), (var(1), 'Alice')}}, 2)
        cls.with_one = State({"eq": {(var(0), 'Dum')}}, 1)
        cls.with_two = State({"eq": {(var(0), 'Dum'), (var(1), 'Dee')}}, 2)

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

class Test_Walk(Test_State_Fixtures):
    def test_walk_one_level(self):
        result = walk(var(0), self.with_one.constraints["eq"])
        self.assertEqual(result, 'Dum')

    def test_walk_two_levels(self):
        result = walk(var(1), self.alice_linked.constraints["eq"])
        self.assertEqual(result, 'Alice')

    def test_walk_var_missing(self):
        result = walk(var(1), self.with_one.constraints["eq"])
        self.assertEqual(result, var(1))

class Test_ext_s(Test_State_Fixtures):
    def test_extend_substitution(self):
        substitution_with_dee = ext_s(var(1), 'Dee', self.with_one.constraints["eq"])
        state_with_dee = State({"eq":substitution_with_dee}, 2)
        self.assertEqual(state_with_dee, self.with_two)

class Test_mzero(unittest.TestCase):
    def test_zero_is_none(self):
        self.assertEqual(list(mzero), [])

class Test_unit(Test_State_Fixtures):
    def test_unit_returns_state(self):
        self.assertEqual(list(unit(self.just_alice)), [self.just_alice])

class Test_unify_fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.empty = frozenset()
        cls.just_alice = {(var(0), 'Alice')}
        cls.alice_linked = {(var(0), 'Alice'), (var(1), var(0))}
        cls.two_alices = {(var(0), 'Alice'), (var(1), 'Alice')}
        cls.with_one = {(var(0), 'Dum')}
        cls.with_two = {(var(0), 'Dum'), (var(1), 'Dee')}

class Test_unify(Test_unify_fixtures):
    def test_eq_constants(self):
        new_substitution = unify(3, 3, self.just_alice)
        self.assertEqual(new_substitution, self.just_alice)

    def test_uneq_constants(self):
        new_substitution = unify(2, 3, self.just_alice)
        self.assertEqual(new_substitution, False)

    def test_var_to_empty(self):
        new_substitution = unify(var(0), 'Alice', self.empty)
        self.assertEqual(new_substitution, self.just_alice)

    def test_var_on_left_new(self):
        new_substitution = unify(var(1), 'Dee', self.with_one)
        self.assertEqual(new_substitution, self.with_two)

    def test_var_on_left_with_constant(self):
        new_substitution = unify(var(1), 'Alice', self.just_alice)
        self.assertEqual(new_substitution, self.two_alices)

    def test_var_on_left_with_var(self):
        new_substitution = unify(var(1), var(0), self.just_alice)
        self.assertEqual(new_substitution, self.alice_linked)

    def test_var_on_left_wrong_with_constant(self):
        new_substitution = unify(var(0), 'Dee', self.with_one)
        self.assertEqual(new_substitution, False)

    def test_var_on_right_new(self):
        new_substitution = unify('Dee', var(1), self.with_one)
        self.assertEqual(new_substitution, self.with_two)

    def test_var_on_right_with_constant(self):
        new_substitution = unify('Alice', var(1), self.just_alice)
        self.assertEqual(new_substitution, self.two_alices)

    def test_var_on_right_with_var(self):
        new_substitution = unify(var(0), var(1), self.just_alice)
        self.assertEqual(new_substitution, self.alice_linked)

    def test_var_on_right_wrong_with_constant(self):
        new_substitution = unify('Dee', var(0), self.with_one)
        self.assertEqual(new_substitution, False)

    def test_var_on_wrong_with_var(self):
        new_substitution = unify(var(0), var(1), self.with_two)
        self.assertEqual(new_substitution, False)

    def test_same_var(self):
        new_substitution = unify(var(1), var(1), self.just_alice)
        self.assertEqual(new_substitution, self.just_alice)

    def test_list_matches(self):
        new_substitution = unify(list_to_links(['Dee', 'Dum']), list_to_links(['Dee', var(0)]), self.with_one)
        self.assertEqual(new_substitution, self.with_one)

    def test_list_matches_with_new(self):
        new_substitution = unify(list_to_links([var(1), 'Dum']), list_to_links(['Dee', var(0)]), self.with_one)
        self.assertEqual(new_substitution, self.with_two)

    def test_list_not_matches(self):
        new_substitution = unify(list_to_links(['Dee', 'Raven']), list_to_links(['Dee', var(0)]), self.with_one)
        self.assertEqual(new_substitution, False)

    def test_list_empties(self):
        new_substitution = unify(Link(), Link().tail, self.empty)
        self.assertEqual(new_substitution, self.empty)


class Test_eq(Test_State_Fixtures):
    def test_eq_constants(self):
        new_states = list(eq(3, 3)(self.just_alice))
        self.assertEqual(len(new_states), 1)
        self.assertEqual(new_states[0], self.just_alice)

    def test_uneq_constants(self):
        new_states = list(eq(2, 3)(self.just_alice))
        self.assertEqual(len(new_states), 0)

    def test_eq_with_var(self):
        new_states = list(eq(var(0), "Alice")(self.just_alice))
        self.assertEqual(len(new_states), 1)
        self.assertEqual(new_states[0], self.just_alice)

class Test_mplus(Test_State_Fixtures):
    def test_two_states(self):
        stream = list(mplus(unit(self.just_alice), unit(self.with_one)))
        self.assertEqual(stream, [self.just_alice, self.with_one])

    def test_first_stream_has_two(self):
        stream = list(mplus(iter([self.with_one, self.with_two]), unit(self.just_alice)))
        self.assertEqual(stream, [self.with_one, self.just_alice, self.with_two])

    def test_second_stream_has_two(self):
        stream = list(mplus(unit(self.just_alice), iter([self.with_one, self.with_two])))
        self.assertEqual(stream, [self.just_alice, self.with_one, self.with_two])

    def test_both_have_two(self):
        stream1 = iter([self.with_one, self.with_two])
        stream2 = iter([self.just_alice, self.alice_linked])
        stream = list(mplus(stream1, stream2))
        self.assertEqual(stream, [self.with_one, self.just_alice, self.with_two, self.alice_linked])

class Test_Disj_Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.just_alice = State({"eq": {(var(0), 'Alice')}}, 2)
        cls.alice_with_dee = State({"eq": {(var(0), 'Alice'), (var(1), 'Dee')}}, 2)
        cls.alice_with_dum = State({"eq": {(var(0), 'Alice'), (var(1), 'Dum')}}, 2)

class Test_disj(Test_Disj_Fixtures):
    def test_alternate_eqs(self):
        states = list(disj(eq(var(1), 'Dee'), eq(var(1), 'Dum'))(self.just_alice))
        self.assertEqual(len(states), 2)
        self.assertEqual(states, [self.alice_with_dee, self.alice_with_dum])

    def test_nested_alternate_eqs(self):
        states = list(disj(eq(var(0), 'Alice'), disj(eq(var(1), 'Dee'), eq(var(1), 'Dum')))(self.just_alice))
        self.assertEqual(len(states), 3)
        self.assertEqual(states, [self.just_alice, self.alice_with_dee, self.alice_with_dum])

class Test_Bind_Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.empty = State({}, 3)
        cls.just_alice = State({"eq": {(var(0), 'Alice')}}, 3)
        cls.alice_linked = State({"eq": {(var(0), 'Alice'), (var(1), var(0))}}, 3)
        cls.two_alices = State({"eq": {(var(0), 'Alice'), (var(1), 'Alice')}}, 3)
        cls.with_one = State({"eq": {(var(0), 'Dum')}}, 3)
        cls.with_two = State({"eq": {(var(0), 'Dum'), (var(1), 'Dee')}}, 3)
        cls.alice_with_boys = State({"eq": {(var(0), 'Alice'), (var(1), 'Dum'), (var(2), 'Dee')}}, 3)
        cls.alice_with_dee = State({"eq": {(var(0), 'Alice'), (var(1), 'Dee')}}, 3)
        cls.alice_with_dum = State({"eq": {(var(0), 'Alice'), (var(1), 'Dum')}}, 3)
        cls.alice_with_raven = State({"eq": {(var(0), 'Alice'), (var(1), 'Raven')}}, 3)

class Test_bind(Test_Bind_Fixtures):
    def test_from_empty(self):
        streams = list(bind(eq(var(0), 'Dum'), eq(var(1), 'Dee'))(self.empty))
        self.assertEqual(len(streams), 1)
        self.assertEqual(streams, [self.with_two])

    def test_with_existing(self):
        streams = list(bind(eq(var(1), 'Dum'), eq(var(2), 'Dee'))(self.just_alice))
        self.assertEqual(len(streams), 1)
        self.assertEqual(streams, [self.alice_with_boys])

    def test_with_nested_bind(self):
        streams = list(bind(eq(var(0), 'Alice'), bind(eq(var(1), 'Dum'), eq(var(2), 'Dee')))(self.empty))
        self.assertEqual(len(streams), 1)
        self.assertEqual(streams, [self.alice_with_boys])

    def test_first_fails(self):
        streams = list(bind(eq(var(0), 'Dee'), eq(var(1), 'Dee'))(self.with_two))
        self.assertEqual(len(streams), 0)
        self.assertEqual(streams, [])

class Test_conj(Test_Bind_Fixtures):
    def test_nested_with_disj(self):
        streams = list(conj(eq(var(0), 'Alice'), disj(eq(var(1), 'Dum'), eq(var(1), 'Dee')))(self.empty))
        self.assertEqual(len(streams), 2)
        self.assertEqual(streams, [self.alice_with_dum, self.alice_with_dee])

    def test_nested_with_3_disj(self):
        streams = list(conj(eq(var(0), 'Alice'), disj(eq(var(1), 'Dum'), disj(eq(var(1), 'Dee'), eq(var(1), 'Raven'))))(self.empty))
        self.assertEqual(len(streams), 3)
        self.assertEqual(streams, [self.alice_with_dum, self.alice_with_dee, self.alice_with_raven])

    def test_second_fails(self):
        streams = list(conj(eq(var(0), 'Dum'), eq(var(1), 'Dum'))(self.with_two))
        self.assertEqual(len(streams), 0)
        self.assertEqual(streams, [])

class Test_call_fresh_Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.empty = State({}, 0)
        cls.spoilt = State({"eq": {(var(0, 'rattle'), 'old')}}, 1)

class Test_call_fresh(Test_call_fresh_Fixtures):
    def test_successful(self):
        states = list(call_fresh(lambda rattle: eq(rattle, 'old'))(self.empty))
        self.assertEqual(len(states), 1)
        self.assertEqual(states, [self.spoilt])

    def test_fails(self):
        states = list(call_fresh(lambda rattle: conj(eq(rattle, 'old'), eq(rattle, 'new')))(self.empty))
        self.assertEqual(len(states), 0)

class Test_neq(Test_State_Fixtures):
    def test_from_empty(self):
        states = list(call_fresh(lambda rattle: neq(rattle, 'new'))(self.empty))
        self.assertEqual(len(states), 1)
        state = states[0]
        self.assertEqual(len(state.constraints), 1)
        self.assertEqual(state.constraints['neq'], {(var(0, 'rattle'), 'new')})

    def test_fail_eq_before(self):
        states = list(call_fresh(lambda rattle: conj(eq(rattle, 'new'), neq(rattle, 'new')))(self.empty))
        self.assertEqual(len(states), 0)

    def test_fail_eq_after(self):
        states = list(call_fresh(lambda rattle: conj(neq(rattle, 'new'), eq(rattle, 'new')))(self.empty))
        self.assertEqual(len(states), 0)

    def test_valid_eq_same_var(self):
        states = list(call_fresh(lambda rattle: conj(neq(rattle, 'new'), eq(rattle, 'old')))(self.empty))
        self.assertEqual(len(states), 1)
        state = states[0]
        self.assertEqual(len(state.constraints), 2)
        self.assertEqual(state.constraints['eq'], {(var(0, 'rattle'), 'old')})
        self.assertEqual(state.constraints['neq'], {(var(0, 'rattle'), 'new')})

class Test_absento(Test_State_Fixtures):
    def test_from_empty(self):
        states = list(call_fresh(lambda boys: absento('raven', boys))(self.empty))
        self.assertEqual(len(states), 1)
        state = states[0]
        self.assertEqual(len(state.constraints), 1)
        self.assertEqual(state.constraints['absento'], {('raven', var(0, 'boys'))})

    def test_fail_scalar_eq_first(self):
        states = list(call_fresh(lambda girl: conj(eq('alice', girl), absento('alice', girl)))(self.empty))
        self.assertEqual(len(states), 0)

    def test_fail_scalar_eq_second(self):
        states = list(call_fresh(lambda girl: conj(absento('alice', girl), eq('alice', girl)))(self.empty))
        self.assertEqual(len(states), 0)

    def test_fail_list_eq_first(self):
        lst = list_to_links(['dum', 'dee'])
        states = list(call_fresh(lambda boys: conj(eq(lst, boys), absento('dee', boys)))(self.empty))
        self.assertEqual(len(states), 0)

    def test_fail_list_eq_second(self):
        lst = list_to_links(['dum', 'dee'])
        states = list(call_fresh(lambda boys: conj(absento('dee', boys), eq(lst, boys)))(self.empty))
        self.assertEqual(len(states), 0)

    def test_succeed_list_eq(self):
        lst = list_to_links(['dum', 'dee'])
        states = list(call_fresh(lambda boys: conj(absento('raven', boys), eq(lst, boys)))(self.empty))
        self.assertEqual(len(states), 1)
        state = states[0]
        self.assertEqual(len(state.constraints), 2)
        self.assertEqual(state.constraints['absento'], {('raven', var(0, 'boys'))})
        self.assertEqual(state.constraints['eq'], {(var(0, 'boys'), lst)})

if __name__ == "__main__":
    print("This test suite depends on macros to execute, so can't be")
    print("run independently. Please either run it through `run_tests.py`")
    print("above, or by importing it in a separate file.")
