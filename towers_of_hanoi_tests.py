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
        states = list(call_fresh(lambda x: lt(x, 4))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(len(states[0].constraints['lt']), 1)

    def test_basic_var_more(self):
        states = list(call_fresh(lambda x: lt(3, x))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(len(states[0].constraints['lt']), 1)

    def test_basic_vars(self):
        states = list(call_fresh_x(lambda x, y: lt(x, y))(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(len(states[0].constraints['lt']), 1)


if __name__ == "__main__":
    unittest.main()
