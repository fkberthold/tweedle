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

class Test_Set_Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var1 = LVar()
        cls.var2 = LVar()
        cls.var3 = LVar()
        cls.queens = {'Red Queen', 'White Queen', 'Queen of Hearts', 'Alice'}
        cls.croquet_players = {'Queen of Hearts', 'Alice'}
        cls.chess_pieces = {'Red Queen', 'White Queen', 'White King', 'White Knight'}

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


class Test_Appendo(Test_List_Fixtures):
    def test_all_constant_succeeds(self):
        result = list(appendo(self.tea_party, 'Alice', self.tea_party + ['Alice']).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_all_constant_fails(self):
        result = list(appendo(self.tea_party, 'Alice', self.tea_party).run())
        self.assertEqual(result, [])

    def test_all_constant_fails_empty_list_with_member(self):
        result = list(appendo([], 'Alice', []).run())
        self.assertEqual(result, [])

    def test_var_member(self):
        result = list(appendo(self.tea_party, self.var1, self.tea_party + ['Alice']).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 'Alice')

    def test_var_member_fails(self):
        result = list(appendo(self.tea_party, self.var1, self.tea_party).run())
        self.assertEqual(result, [])

    def test_var_member_fails_empty_list_with_member(self):
        result = list(appendo([], self.var1, []).run())
        self.assertEqual(result, [])

    def test_var_lst(self):
        result = list(appendo(self.var1, 'Alice', self.tea_party + ['Alice']).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], self.tea_party)

    def test_var_lst_fails(self):
        result = list(appendo(self.var1, 'Alice', self.tea_party).run())
        self.assertEqual(result, [])

    def test_var_lst_fails_empty_lst_with_member(self):
        result = list(appendo(self.var1, 'Alice', []).run())
        self.assertEqual(result, [])

    def test_var_lst_with_member(self):
        result = list(appendo(self.tea_party, 'Alice', self.var1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], self.tea_party + ['Alice'])

    def test_var_lst_and_member(self):
        result = list(appendo(self.var1, self.var2, self.tea_party + ['Alice']).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], self.tea_party)
        self.assertEqual(result[0][self.var2], 'Alice')

    def test_var_lst_and_member_fails(self):
        result = list(appendo(self.var1, self.var2, []).run())
        self.assertEqual(result, [])

    def test_var_lst_and_lst_with_member(self):
        results = list(appendo(self.var1, 'Alice', self.var2).run(results=2))
        self.assertEqual(len(results), 2)
        lst_empty = results[0]
        lst_one = results[1]
        self.assertEqual(lst_empty[self.var1], [])
        self.assertEqual(lst_empty[self.var2], ['Alice'])
        self.assertEqual(len(lst_one[self.var1]), 1)
        self.assertEqual(len(lst_one[self.var2]), 2)
        self.assertEqual(lst_one[self.var1][0], lst_one[self.var2][0])
        self.assertEqual(lst_one[self.var2][1], 'Alice')

class Test_Indexo(Test_List_Fixtures):
    def test_all_constant_succeeds(self):
        result = list(indexo(self.tea_party, 0, 'Mad Hatter').run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_all_constant_fails_out_of_bounds(self):
        result = list(indexo(self.tea_party, 3, 'The Dormouse').run())
        self.assertEqual(len(result), 0)

    def test_all_constant_fails_wrong_value(self):
        result = list(indexo(self.tea_party, 0, 'March Hare').run())
        self.assertEqual(len(result), 0)

    def test_var_index(self):
        result = list(indexo(self.tea_party, self.var1, 'March Hare').run())
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][self.var1], 1)
        self.assertEqual(result[1][self.var1], -2)

    def test_var_value(self):
        result = list(indexo(self.tea_party, 2, self.var1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], 'The Dormouse')

    def test_var_value_index_out_of_range(self):
        result = list(indexo(self.tea_party, 3, self.var1).run())
        self.assertEqual(len(result), 0)

    def test_var_lst(self):
        result = list(indexo(self.var1, 1, 'Mad Hatter').run(results=2))
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
        result = list(indexo(self.dinner_party, self.var2, self.var1).run())
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
        results = list(indexo(self.var1, self.var2, 'Alice').run(results=6))
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
        results = list(indexo(self.var1, self.var2, self.var3).run(results=6))
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

class Test_Sliceo(Test_List_Fixtures):
    def test_constant_succeeds(self):
        result = list(sliceo(self.tea_party, 1, 3, ['March Hare', 'The Dormouse']).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], State())

    def test_constant_fails(self):
        result = list(sliceo(self.tea_party, 0, 3, ['Mad Hatter', 'March Hare', 'The Dormouse', 'Alice']).run())
        self.assertEqual(len(result), 0)

    def test_var_end(self):
        results = list(sliceo(self.tea_party, 1, self.var1, ['March Hare', 'The Dormouse']).run(results=3))
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0][self.var1], None)
        self.assertEqual(results[1][self.var1], 3)
        self.assertEqual(results[2][self.var1], 4)

    def test_var_end_just_front(self):
        results = list(sliceo(self.tea_party, 0, self.var1, ['Mad Hatter', 'March Hare']).run())
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][self.var1], 2)
        self.assertEqual(results[1][self.var1], -1)

    def test_var_end_fail(self):
        results = list(sliceo(self.tea_party, 2, self.var1, ['March Hare', 'The Dormouse']).run(results=3))
        self.assertEqual(len(results), 0)

    def test_var_start(self):
        results = list(sliceo(self.tea_party, self.var1, 3, ['March Hare', 'The Dormouse']).run())
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][self.var1], 1)
        self.assertEqual(results[1][self.var1], -2)

    def test_var_start_from_beginning(self):
        results = list(sliceo(self.tea_party, self.var1, 2, ['Mad Hatter', 'March Hare']).run(results=3))
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0][self.var1], None)
        self.assertEqual(results[1][self.var1], 0)
        self.assertEqual(results[2][self.var1], -3)

    def test_var_start_too_long_fail(self):
        results = list(sliceo(self.tea_party, self.var1, 2, ['Mad Hatter', 'March Hare', 'The Dormouse', 'Alice']).run(results=3))
        self.assertEqual(len(results), 0)

    def test_var_sublist(self):
        result = list(sliceo(self.tea_party, 1, 3, self.var1).run())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][self.var1], self.tea_party[1:3])

    def test_var_list_indexes_none_none(self):
        results = list(sliceo(self.var1, None, None, self.tea_party[None:None]).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][self.var1], self.tea_party)

    def test_var_list_indexes_none_pos(self):
        results = list(sliceo(self.var1, None, 3, self.tea_party[None:3]).run(results=2))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][self.var1], self.tea_party)
        self.assertEqual(len(results[1][self.var1]), 4)
        self.assertEqual(results[1][self.var1][0:3], self.tea_party)
        self.assertTrue(varq(results[1][self.var1][3]))

    def test_var_list_indexes_none_neg(self):
        results = list(sliceo(self.var1, None, -1, self.tea_party[None:-1]).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0][self.var1]), 3)
        self.assertEqual(results[0][self.var1][None:-1], self.tea_party[None:-1])
        self.assertTrue(varq(results[0][self.var1][2]))

    def test_var_list_indexes_pos_none(self):
        results = list(sliceo(self.var1, 1, None, self.tea_party[1:None]).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0][self.var1]), 3)
        self.assertEqual(results[0][self.var1][1:None], self.tea_party[1:None])
        self.assertTrue(varq(results[0][self.var1][0]))

    def test_var_list_indexes_pos_pos(self):
        results = list(sliceo(self.var1, 1, 3, self.tea_party[1:3]).run(results=2))
        self.assertEqual(len(results), 2)
        self.assertEqual(len(results[0][self.var1]), 3)
        self.assertTrue(varq(results[0][self.var1][0]))
        self.assertEqual(results[0][self.var1][1:3], self.tea_party[1:3])
        self.assertEqual(len(results[1][self.var1]), 4)
        self.assertTrue(varq(results[1][self.var1][0]))
        self.assertEqual(results[1][self.var1][1:3], self.tea_party[1:3])
        self.assertTrue(varq(results[1][self.var1][3]))

    def test_var_list_indexes_pos_neg(self):
        results = list(sliceo(self.var1, 1, -1, self.tea_party[1:-1]).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0][self.var1]), 3)
        self.assertTrue(varq(results[0][self.var1][0]))
        self.assertEqual(results[0][self.var1][1:-1], self.tea_party[1:-1])
        self.assertTrue(varq(results[0][self.var1][2]))

    def test_var_list_indexes_neg_none(self):
        results = list(sliceo(self.var1, -2, None, self.tea_party[-2:None]).run(results=2))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][self.var1], self.tea_party[-2:None])
        self.assertEqual(len(results[1][self.var1]), 3)
        self.assertTrue(varq(results[1][self.var1][0]))
        self.assertEqual(results[1][self.var1][-2:None], self.tea_party[-2:None])

    def test_var_list_indexes_neg_pos(self):
        results = list(sliceo(self.var1, -2, 3, self.tea_party[-2:3]).run())
        self.assertEqual(len(results), 2)
        self.assertEqual(len(results[0][self.var1]), 2)
        self.assertEqual(results[0][self.var1], self.tea_party[1:3])
        self.assertEqual(len(results[1][self.var1]), 3)
        self.assertTrue(varq(results[1][self.var1][0]))
        self.assertEqual(results[1][self.var1][1:3], self.tea_party[1:3])

    def test_var_list_indexes_neg_neg(self):
        results = list(sliceo(self.var1, -2, -1, self.tea_party[-2:-1]).run(results=2))
        self.assertEqual(len(results), 2)
        self.assertEqual(len(results[0][self.var1]), 2)
        self.assertEqual(results[0][self.var1][-2:-1], self.tea_party[-2:-1])
        self.assertTrue(varq(results[0][self.var1][-1]))
        self.assertEqual(len(results[1][self.var1]), 3)
        self.assertTrue(varq(results[1][self.var1][0]))
        self.assertEqual(results[1][self.var1][-2:-1], self.tea_party[-2:-1])
        self.assertTrue(varq(results[1][self.var1][-1]))

    def test_var_list_indexes_none_pos_past_end(self):
        results = list(sliceo(self.var1, None, 1, self.tea_party).run())
        self.assertEqual(len(results), 0)

    def test_var_list_indexes_pos_pos_sublist_too_long(self):
        results = list(sliceo(self.var1, 1, 2, self.tea_party).run())
        self.assertEqual(len(results), 0)

    def test_var_list_indexes_pos_pos_length_out_of_bounds(self):
        results = list(sliceo(self.var1, 1, 4, self.tea_party).run(results=1))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0][self.var1]), 4)
        self.assertTrue(varq(results[0][self.var1][0]))
        self.assertEqual(results[0][self.var1][1:4], self.tea_party)

    def test_var_list_indexes_neg_none_too_short(self):
        results = list(sliceo(self.var1, -2, None, self.tea_party).run())
        self.assertEqual(len(results), 0)

    def test_var_list_indexes_neg_pos_too_short(self):
        results = list(sliceo(self.var1, -1, 1, self.tea_party).run())
        self.assertEqual(len(results), 0)

    def test_var_list_indexes_neg_neg_makes_empty(self):
        results = list(sliceo(self.var1, -1, -2, self.tea_party).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0][self.var1]), 0)

    def test_more_than_one_var(self):
        results = list(sliceo(self.tea_party, self.var1, self.var2, ["March Hare", "The Dormouse"]).run(results=4))
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertEqual(self.tea_party[result[self.var1]:result[self.var2]], ["March Hare", "The Dormouse"])

class Test_Rangeo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.var = LVar()

    def test_no_limit_constant(self):
        results = list(rangeo(3, None, None).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], State())

    def test_from_start_constant_succeed(self):
        results = list(rangeo(3, -2, None).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], State())

    def test_from_start_constant_fail(self):
        results = list(rangeo(-3, -2, None).run())
        self.assertEqual(len(results), 0)

    def test_from_end_constant_succeed(self):
        results = list(rangeo(-1, None, 2).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], State())

    def test_from_end_constant_fail(self):
        results = list(rangeo(2, None, 2).run())
        self.assertEqual(len(results), 0)

    def test_between_start_end_constant_succeed(self):
        results = list(rangeo(-1, -1, 2).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], State())

    def test_between_start_end_constant_fail(self):
        results = list(rangeo(2, -1, 2).run())
        self.assertEqual(len(results), 0)

    def test_no_limit_var(self):
        results = list(rangeo(self.var, None, None).run(results=4))
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0][self.var], 0)
        self.assertEqual(results[1][self.var], 1)
        self.assertEqual(results[2][self.var], -1)
        self.assertEqual(results[3][self.var], 2)

    def test_from_start_var_succeed(self):
        results = list(rangeo(self.var, -1, None).run(results=2))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][self.var], -1)
        self.assertEqual(results[1][self.var], 0)

    def test_from_end_var_succeed(self):
        results = list(rangeo(self.var, None, 1).run(results=2))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][self.var], 0)
        self.assertEqual(results[1][self.var], -1)

    def test_between_start_end_var_succeed(self):
        results = list(rangeo(self.var, -2, 1).run())
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0][self.var], -2)
        self.assertEqual(results[1][self.var], -1)
        self.assertEqual(results[2][self.var], 0)

class Test_Set_Leno(Test_Set_Fixtures):
    def test_constant_succeed(self):
        results = list(set_leno(self.queens, 4).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], State())

    def test_constant_fail(self):
        results = list(set_leno(self.queens, 5).run())
        self.assertEqual(len(results), 0)

    def test_set_succeed(self):
        results = list(set_leno(self.var1, 3).run())
        self.assertEqual(len(results), 1)
        self.assertTrue(all([varq(value) for value in results[0][self.var1]]))

    def test_length_succeed(self):
        results = list(set_leno(self.queens, self.var1).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][self.var1], 4)

    def test_both_succeed(self):
        results = list(set_leno(self.var1, self.var2).run(results=3))
        self.assertEqual(len(results), 3)
        for (result, length) in zip(results, range(0, 3)):
            self.assertEqual(len(result[self.var1]), length)
            self.assertEqual(result[self.var2], length)
            self.assertTrue(all([varq(value) for value in result[self.var1]]))

class Test_Set_Emptyo(Test_Set_Fixtures):
    def test_constant_succeed(self):
        results = list(set_emptyo(set()).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], State())

    def test_var_succeed(self):
        results = list(set_emptyo(self.var1).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][self.var1], set())

class Test_Set_Membero(Test_Set_Fixtures):
    def test_constant_succeed(self):
        results = list(set_membero(self.queens, 'Alice').run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], State())

    def test_constant_succeed(self):
        results = list(set_membero(self.queens, 'Dinah').run())
        self.assertEqual(len(results), 0)

    def test_set_with_vars_constant_matches(self):
        results = list(set_membero({'Spades', 'Clubs', self.var1, self.var2}, 'Spades').run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], State())

    def test_set_with_vars_var_matches(self):
        results = list(set_membero({'Spades', 'Clubs', self.var1, self.var2}, 'Hearts').run())
        self.assertEqual(len(results), 2)
        self.assertTrue(any([result[self.var1] == 'Hearts' for result in results]))
        self.assertTrue(any([result[self.var2] == 'Hearts' for result in results]))
        self.assertTrue(not any([result[self.var1] == 'Hearts' and result[self.var2] == 'Hearts' for result in results]))

    def test_set_with_var_has_same_var(self):
        results = list(set_membero({'Dinah', self.var1}, self.var1).run())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], State())

    def test_set_and_var(self):
        results = list(set_membero(self.queens, self.var1).run())
        self.assertEqual(len(results), 4)
        self.assertEqual(self.queens, {result[self.var1] for result in results})

    def test_set_is_var(self):
        results = list(set_membero(self.var1, 'Dinah').run(results=4))
        self.assertEqual(len(results), 4)
        self.assertEqual(len(results[0][self.var1]), 1)
        self.assertEqual(len(results[1][self.var1]), 2)
        self.assertEqual(len(results[2][self.var1]), 2)
        self.assertEqual(len(results[3][self.var1]), 3)
        for result in results:
            a_set = result[self.var1]
            self.assertTrue(any([result[val] == 'Dinah' for val in a_set]))

if __name__ == "__main__":
    print("This test suite depends on macros to execute, so can't be")
    print("run independently. Please either run it through `run_tests.py`")
    print("above, or by importing it in a separate file.")
