import os.path
import sys
import unittest
from microkanren.ukanren import *
from microkanren.collections import *
from microkanren.macro import macros, conj, disj, goal, call

class Test_List_Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()
        cls.var3 = LVar()
        cls.dinner_party = ['The Walrus', 'The Carpenter']
        cls.tea_party = ['Mad Hatter', 'March Hare', 'The Dormouse']


class Test_List_Emptyo(Test_List_Fixtures):
    def test_empty(self):
        result = list(list_emptyo([]).run())
        self.assertEqual(result, [State()])

    def test_not_empty(self):
        result = list(list_emptyo([3]).run())
        self.assertEqual(result, [])

class Test_List_Leno(Test_List_Fixtures):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()

    def test_empty_0(self):
        result = list(list_leno([], 0).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_single_1(self):
        result = list(list_leno(['Alice'], 1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_two_2(self):
        result = list(list_leno(['Dee', 'Dum'], 2).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_empty_x(self):
        result = list(list_leno([], self.var1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 0)

    def test_single_x(self):
        result = list(list_leno(['Alice'], self.var1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 1)

    def test_two_x(self):
        result = list(list_leno(['Dee', 'Dum'], self.var1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 2)

    def test_x_0(self):
        result = list(list_leno(self.var1, 0).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], [])

    def test_x_1(self):
        result = list(list_leno(self.var1, 1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0][self.var1]), 1)
        self.assertTrue(all([varq(v) for v in result[0][self.var1]]))

    def test_x_2(self):
        result = list(list_leno(self.var1, 2).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0][self.var1]), 2)
        self.assertTrue(all([varq(v) for v in result[0][self.var1]]))

    def test_x_y(self):
        result = list(list_leno(self.var1, self.var2).run(results=3))
        self.assertEqual(len(result), 3)
        self.assertEqual(len(result[0][self.var1]), 0)
        self.assertEqual(len(result[1][self.var1]), 1)
        self.assertEqual(len(result[2][self.var1]), 2)
        self.assertTrue(all([varq(v) for st in result for v in st[self.var1]]))


class Test_Indexo(Test_List_Fixtures):
    def test_all_constant_succeeds(self):
        result = list(indexo(self.tea_party, 'Mad Hatter', 0).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_all_constant_fails_out_of_bounds(self):
        result = list(indexo(self.tea_party, 'The Dormouse', 3).run())
        self.assertEqual(len(result), 0)

    def test_all_constant_fails_wrong_value(self):
        result = list(indexo(self.tea_party, 'March Hare', 0).run())
        self.assertEqual(len(result), 0)

    def test_var_index(self):
        result = list(indexo(self.tea_party, 'March Hare', self.var1).run())
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][self.var1], 1)
        self.assertEqual(result[1][self.var1], -2)

    def test_var_value(self):
        result = list(indexo(self.tea_party, self.var1, 2).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 'The Dormouse')

    def test_var_value_index_out_of_range(self):
        result = list(indexo(self.tea_party, self.var1, 3).run())
        self.assertEqual(len(result), 0)

    def test_var_lst(self):
        result = list(indexo(self.var1, 'Mad Hatter', 1).run(results=2))
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0][self.var1]), 2)
        self.assertTrue(varq(result[0][self.var1][0]))
        self.assertEqual(result[0][self.var1][1], 'Mad Hatter')

        self.assertEqual(len(result[1][self.var1]), 3)
        self.assertTrue(varq(result[1][self.var1][0]))
        self.assertEqual(result[1][self.var1][1], 'Mad Hatter')
        self.assertTrue(varq(result[1][self.var1][2]))
        self.assertNotEqual(result[1][self.var1][0], result[1][self.var1][2])

    def test_var_value_and_index(self):
        result = list(indexo(self.dinner_party, self.var1, self.var2).run())
        self.assertEqual(len(result), 4)
        walrus_pos = result[0]
        walrus_neg = result[1]
        carpenter_pos = result[2]
        carpenter_neg = result[3]
        self.assertEqual(self.dinner_party[walrus_pos[self.var2]], walrus_pos[self.var1])
        self.assertEqual(self.dinner_party[walrus_neg[self.var2]], walrus_neg[self.var1])
        self.assertEqual(self.dinner_party[carpenter_pos[self.var2]], carpenter_pos[self.var1])
        self.assertEqual(self.dinner_party[carpenter_neg[self.var2]], carpenter_neg[self.var1])

    def test_var_lst_and_index(self):
        results = list(indexo(self.var1, 'Alice', self.var2).run(results=6))
        self.assertEqual(len(results), 6)
        alice_1_first_pos = results[0]
        alice_1_first_neg = results[1]
        alice_2_first_pos = results[2]
        alice_2_first_neg = results[3]
        alice_2_second_pos = results[4]
        alice_2_second_neg = results[5]

        result = alice_1_first_pos
        self.assertEqual(len(result[self.var1]), 1)
        self.assertEqual(result[self.var2], 0)
        result = alice_1_first_neg
        self.assertEqual(len(result[self.var1]), 1)
        self.assertEqual(result[self.var2], -1)
        result = alice_2_first_pos
        self.assertEqual(len(result[self.var1]), 2)
        self.assertEqual(result[self.var2], 0)
        result = alice_2_first_neg
        self.assertEqual(len(result[self.var1]), 2)
        self.assertEqual(result[self.var2], -2)
        result = alice_2_second_pos
        self.assertEqual(len(result[self.var1]), 2)
        self.assertEqual(result[self.var2], 1)
        result = alice_2_second_neg
        self.assertEqual(len(result[self.var1]), 2)
        self.assertEqual(result[self.var2], -1)

        for result in results:
            self.assertEqual(result[self.var1][result[self.var2]], 'Alice')

    def test_var_all(self):
        results = list(indexo(self.var1, self.var3, self.var2).run(results=6))
        self.assertEqual(len(results), 6)
        var_1_first_pos = results[0]
        var_1_first_neg = results[1]
        var_2_first_pos = results[2]
        var_2_first_neg = results[3]
        var_2_second_pos = results[4]
        var_2_second_neg = results[5]

        result = var_1_first_pos
        self.assertEqual(len(result[self.var1]), 1)
        self.assertEqual(result[self.var2], 0)
        result = var_1_first_neg
        self.assertEqual(len(result[self.var1]), 1)
        self.assertEqual(result[self.var2], -1)
        result = var_2_first_pos
        self.assertEqual(len(result[self.var1]), 2)
        self.assertEqual(result[self.var2], 0)
        result = var_2_first_neg
        self.assertEqual(len(result[self.var1]), 2)
        self.assertEqual(result[self.var2], -2)
        result = var_2_second_pos
        self.assertEqual(len(result[self.var1]), 2)
        self.assertEqual(result[self.var2], 1)
        result = var_2_second_neg
        self.assertEqual(len(result[self.var1]), 2)
        self.assertEqual(result[self.var2], -1)

        for result in results:
            self.assertEqual(result[self.var1][result[self.var2]], result[self.var3])


if __name__ == "__main__":
    print("This test suite depends on macros to execute, so can't be")
    print("run independently. Please either run it through `run_tests.py`")
    print("above, or by importing it in a separate file.")
