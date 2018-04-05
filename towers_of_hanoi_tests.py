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

class Test_Conso(Test_Conso_Fixtures):
    def test_constant_valid(self):
        states = list(conso("Alice", self.empty_link, self.alice_alone)(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states, [self.empty_state])

    def test_empty_tail(self):
        states = list(eq(self.empty_link, self.alice_alone.tail)(self.empty_state))
        self.assertEqual(len(states), 1)
        self.assertEqual(states, [self.empty_state])

if __name__ == "__main__":
    unittest.main()
