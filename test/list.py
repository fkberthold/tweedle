import os.path
import sys
import unittest
from microkanren.urkanren import *
from microkanren.list import *

empty_state = State()

one_value = State({var(0):'hi'}, 1)
two_values = State({var(0):'hi', var(1):'bye'}, 2)
value_reference = State({var(0):var(1), var(1):'bye'}, 2)
identical_values = State({var(0):'hi', var(1):'hi'}, 2)

class Test_MicroKanrenLists(unittest.TestCase):
    def test_heado_known_both(self):
        self.assertCountEqual(list(heado(['hi', 'bye'], 'hi')(one_value)), [one_value])

    def test_heado_doesnt_resolve(self):
        self.assertCountEqual(list(heado(['hi', 'bye'], 'bye')(one_value)), [])

    def test_heado_unknown_head(self):
        self.assertCountEqual(list(call_fresh(lambda x: heado(['bye', 'hi'], x))(one_value)), [two_values])

    def test_heado_unknown_list(self):
        result = State({var(1): ['hi'], **one_value.substitution}, 2)
        self.assertEqual((call_fresh(lambda x: heado(x, 'hi'))(one_value)).__next__(), result)

    def test_heado_unknown_both(self):
        result = State({var(0): [var(1)]}, 2)
        self.assertEqual((call_fresh(lambda x, y: heado(x, y))(empty_state)).__next__(), result)

    def test_tailo_known_both(self):
        self.assertCountEqual(list(tailo(['hi', 'bye'], ['bye'])(one_value)), [one_value])

    def test_tailo_doesnt_resolve(self):
        self.assertCountEqual(list(tailo(['hi', 'bye'], ['hi'])(one_value)), [])

    def test_tailo_unknown_tail(self):
        self.assertCountEqual(list(call_fresh(lambda x: tailo(['hi', 'bye'], [x]))(one_value)), [two_values])

    def test_tailo_unknown_tail(self):
        self.assertCountEqual(list(call_fresh(lambda x: tailo(['hi', 'bye'], [x]))(one_value)), [two_values])

if __name__ == "__main__":
    unittest.main()
