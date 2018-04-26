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
        self.assertEqual(answer, [Link('Alice')])

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
        self.assertEqual(states[0], [Link('dee')])

    def test_first_has_var(self):
        states = list(run_x(lambda dee: appendo(Link(dee), Link('dum'), list_to_links(['dee', 'dum'])))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], ['dee'])

    def test_second_is_var(self):
        states = list(run_x(lambda dum: appendo(Link('dee'), dum, list_to_links(['dee', 'dum'])))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], [Link('dum')])

    def test_second_has_var(self):
        states = list(run_x(lambda dum: appendo(Link('dee'), Link(dum), list_to_links(['dee', 'dum'])))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], ['dum'])

    def test_combined_is_var(self):
        states = list(run_x(lambda deedum: appendo(Link('dee'), Link('dum'), deedum))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], [list_to_links(['dee', 'dum'])])

    def test_combined_has_first_var(self):
        states = list(run_x(lambda dee: appendo(Link('dee'), Link('dum'), list_to_links([dee, 'dum'])))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], ['dee'])

class Test_Addo(Test_Conso_Fixtures):
    def test_addo_const_passes(self):
        states = list(addo(3, 4, 7)(State()))
        self.assertEqual(len(states), 1)

    def test_addo_const_fails(self):
        states = list(addo(3, 4, 8)(State()))
        self.assertEqual(len(states), 0)

    def test_addo_var_total(self):
        states = list(run_x(lambda x: (addo(3, 4, x)))(State()))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], [7])

    def test_addo_var_augend(self):
        states = list(run_x(lambda x: (addo(x, 4, 7)))(State()))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], [3])

    def test_addo_var_addend(self):
        states = list(run_x(lambda x: (addo(3, x, 7)))(State()))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], [4])

    def test_across_two(self):
        states = list(run_x(lambda x:
                            call_fresh(lambda y:
                                       conj_x(addo(y, x, 7),
                                              eq(y, 3))))(State()))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], [4])

class Test_Indexo(Test_Conso_Fixtures):
    def test_indexo_const_just_one_passes(self):
        states = list(indexo(Link('Alice'), 'Alice', 0)(State()))
        self.assertEqual(len(states), 1)

    def test_indexo_const_just_one_fails(self):
        states = list(indexo(Link('Alice'), 'Dinah', 0)(State()))
        self.assertEqual(len(states), 0)

    def test_indexo_just_one_elem_var(self):
        states = list(run_x(lambda name: indexo(Link('Alice'), name, 0))(State()))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], ['Alice'])

    def test_indexo_just_one_index_var(self):
        states = list(run_x(lambda index: indexo(Link('Alice'), 'Alice', index))(State()))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], [0])

    def test_indexo_just_one_lst_var(self):
        states = list(run_x(lambda lst: indexo(lst, 'Alice', 0))(State()))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0][0].head, 'Alice')

    def test_indexo_second_elem_var(self):
        states = list(run_x(lambda name: indexo(list_to_links(['Hatter', 'Hare', 'Dormouse']), name, 1))(State()))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], ['Hare'])

    def test_indexo_third_elem_var(self):
        states = list(run_x(lambda name: indexo(list_to_links(['Hatter', 'Hare', 'Dormouse']), name, 2))(State()))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], ['Dormouse'])

    def test_indexo_second_index_var(self):
        states = list(run_x(lambda index: indexo(list_to_links(['Hatter', 'Hare', 'Dormouse']), 'Hare', index))(State()))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], [1])

    def test_indexo_third_index_var(self):
        states = list(run_x(lambda index: indexo(list_to_links(['Hatter', 'Hare', 'Dormouse']), 'Dormouse', index))(State()))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], [2])

    def test_indexo_more_than_one(self):
        states = list(run_x(lambda index: indexo(list_to_links(['Card', 'Queen', 'Card']), 'Card', index))(State()))
        self.assertEqual(len(states), 2)
        self.assertEqual(states, [[0], [2]])

class Test_Is_Action(Test_Conso_Fixtures):
    pass

if __name__ == "__main__":
    unittest.main()
