import os.path
import sys
import unittest
from microkanren.urconstraintkanren import *
from towers_of_hanoi import *

class Test_Conso_Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.empty_state = State()
        cls.empty_link = Link()
        cls.alice_alone = Link("Alice")
        cls.just_alice = State({"eq": {(var(0), 'Alice')}}, {"eq":eq}, 1)

class Test_Conso(Test_Conso_Fixtures):
    def test_constant_valid(self):
        states = list(conso("Alice", self.empty_link, self.alice_alone)(self.just_alice))
        self.assertEqual(len(states), 1)
        self.assertEqual(states, [self.just_alice])

    def test_empty_tail(self):
        states = list(eq(self.empty_link, self.alice_alone.tail)(self.just_alice))
        self.assertEqual(len(states), 1)
        self.assertEqual(states, [self.just_alice])

    def test_var_head(self):
        states = list(call_fresh(lambda head: conso(head, self.empty_link, self.alice_alone))(self.just_alice))
        self.assertEqual(len(states), 1)
        state = states[0]
        self.assertEqual(len(state.constraints['eq']), 2)

    def test_var_tail(self):
        states = list(call_fresh(lambda tail: conso("Alice", tail, self.alice_alone))(self.just_alice))
        self.assertEqual(len(states), 1)
        state = states[0]
        self.assertEqual(len(state.constraints['eq']), 2)

    def test_var_lst(self):
        states = list(run_x(lambda lst: conso("Alice", self.empty_link, lst))(self.just_alice))
        self.assertEqual(len(states), 1)
        answer = states[0]
        self.assertEqual(answer, {(var(1, 'lst'), list_to_links(['Alice']))})

    def test_fail(self):
        answers = list(run_x(lambda name: conj(eq(name, 'Dinah'), conso(name, self.empty_link, self.alice_alone)))(self.just_alice))
        self.assertEqual(len(answers), 0)

class Test_Lt(Test_Conso_Fixtures):
    def test_constant_less(self):
        states = list(lt(3, 4)(self.just_alice))
        self.assertEqual(len(states), 1)
        self.assertEqual(states, [self.just_alice])

    def test_constant_not_less(self):
        states = list(lt(4, 3)(self.just_alice))
        self.assertEqual(len(states), 0)

    def test_basic_var_less(self):
        states = list(call_fresh(lambda tarts: lt(tarts, 4))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(len(states[0].constraints['lt']), 1)

    def test_basic_var_more(self):
        states = list(call_fresh(lambda tarts: lt(3, tarts))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(len(states[0].constraints['lt']), 1)

    def test_basic_vars(self):
        states = list(call_fresh_x(lambda tarts, oysters: lt(tarts, oysters))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(len(states[0].constraints['lt']), 1)

    def test_less_chain_succeed(self):
        states = list(call_fresh(lambda tarts: conj(lt(tarts, 7), lt(3, tarts)))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(len(states[0].constraints['lt']), 2)

    def test_less_chain_fail(self):
        states = list(call_fresh(lambda tarts: conj(lt(tarts, 3), lt(4, tarts)))(self.empty_state))
        self.assertEqual(len(states), 0)

    def test_more_chain_succeed(self):
        states = list(call_fresh(lambda tarts: conj(lt(3, tarts), lt(tarts, 7)))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(len(states[0].constraints['lt']), 2)

    def test_more_chain_fail(self):
        states = list(call_fresh(lambda tarts: conj(lt(4, tarts), lt(tarts, 3)))(self.empty_state))
        self.assertEqual(len(states), 0)

    def test_eq_after_succeed(self):
        states = list(call_fresh(lambda tarts: conj(lt(3, tarts), eq(tarts, 4)))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(len(states[0].constraints['lt']), 1)

    def test_eq_after_fail(self):
        states = list(call_fresh(lambda tarts: conj(lt(3, tarts), eq(tarts, 3)))(self.empty_state))
        self.assertEqual(len(states), 0)

    def test_bad_loop(self):
        states = list(call_fresh_x(lambda tarts, oysters: conj(lt(tarts, oysters), eq(oysters, tarts)))(self.empty_state))
        self.assertEqual(len(states), 0)

    def test_single_pinned_fail(self):
        states = list(call_fresh(lambda tarts: conj(lt(3, tarts), lt(tarts, 4)))(self.empty_state))
        self.assertEqual(len(states), 0)

    def test_double_pinned_fail(self):
        states = list(call_fresh_x(lambda tarts, oysters: conj_x(lt(3, tarts), lt(tarts, oysters), lt(oysters, 5)))(self.empty_state))
        self.assertEqual(len(states), 0)

class Test_Emptyo(Test_Conso_Fixtures):
    def test_constant_empty(self):
        states = list(emptyo(Link())(self.empty_state))
        self.assertEqual(len(states), 1)

    def test_constant_not_empty(self):
        states = list(emptyo(Link('white knight'))(self.empty_state))
        self.assertEqual(len(states), 0)

class Test_Append(Test_Conso_Fixtures):
    def test_constant_all_empty(self):
        states = list(appendo(Link(), Link(), Link())(self.empty_state))
        self.assertEqual(len(states), 1)

    def test_first_not_empty(self):
        states = list(appendo(Link('alice'), Link(), Link('alice'))(self.empty_state))
        self.assertEqual(len(states), 1)

    def test_second_not_empty(self):
        states = list(appendo(Link(), Link('alice'), Link('alice'))(self.empty_state))
        self.assertEqual(len(states), 1)

    def test_none_empty(self):
        states = list(appendo(Link('dee'), Link('dum'), list_to_links(['dee', 'dum']))(self.empty_state))
        self.assertEqual(len(states), 1)

    def test_first_not_empty_to_empty_fails(self):
        states = list(appendo(Link('alice'), Link(), Link())(self.empty_state))
        self.assertEqual(len(states), 0)

    def test_second_not_empty_to_empty_fails(self):
        states = list(appendo(Link(), Link('alice'), Link())(self.empty_state))
        self.assertEqual(len(states), 0)

    def test_none_empty_to_first_fails(self):
        states = list(appendo(Link('dee'), Link('dum'), Link('dee'))(self.empty_state))
        self.assertEqual(len(states), 0)

    def test_none_empty_to_second_fails(self):
        states = list(appendo(Link('dee'), Link('dum'), Link('dum'))(self.empty_state))
        self.assertEqual(len(states), 0)

    def test_first_is_var(self):
        states = list(run_x(lambda dee: appendo(dee, Link('dum'), list_to_links(['dee', 'dum'])))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], {(var(0, 'dee'), Link('dee'))})

    def test_first_has_var(self):
        states = list(run_x(lambda dee: appendo(Link(dee), Link('dum'), list_to_links(['dee', 'dum'])))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], {(var(0, 'dee'), 'dee')})

    def test_second_is_var(self):
        states = list(run_x(lambda dum: appendo(Link('dee'), dum, list_to_links(['dee', 'dum'])))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], {(var(0, 'dum'), Link('dum'))})

    def test_second_has_var(self):
        states = list(run_x(lambda dum: appendo(Link('dee'), Link(dum), list_to_links(['dee', 'dum'])))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], {(var(0, 'dum'), 'dum')})

    def test_combined_is_var(self):
        states = list(run_x(lambda deedum: appendo(Link('dee'), Link('dum'), deedum))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], {(var(0, 'dum'), list_to_links(['dee', 'dum']))})

    def test_combined_has_first_var(self):
        states = list(run_x(lambda dee: appendo(Link('dee'), Link('dum'), list_to_links([dee, 'dum'])))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], {(var(0, 'dee'), 'dee')})

class Test_Addo(Test_Conso_Fixtures):
    def test_addo_const_passes(self):
        states = list(addo(3, 4, 7)(State()))
        self.assertEqual(len(states), 1)

    def test_addo_const_fails(self):
        states = list(addo(3, 4, 8)(State()))
        self.assertEqual(len(states), 0)

    def test_addo_var_total(self):
        states = list(call_fresh(lambda x: (addo(3, 4, x)))(State()))
        self.assertEqual(len(states), 1)


if __name__ == "__main__":
    unittest.main()
