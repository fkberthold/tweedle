from microkanren.ukanren import *
import copy
import itertools
from microkanren.macro import macros, conj, disj, goal, call
import time

class rangeo(Relation):
    """This is purely a helper class for the list relation.  It will not work
    correctly if start or end are given logic variables."""
    def __init__(self, num, start=None, end=None):
        super().__init__()
        self.num = num
        self.start = start
        self.end = end

    def __run__(self, state):
        num = state.reify(self.num)
        start = state.reify(self.start)
        end = state.reify(self.end)

        if start is None and end is None:
            if varq(num):
                yield from Eq(num, 0).run(state)
                count = 1
                while True:
                    yield from Eq(num, count).run(state)
                    yield from Eq(num, -count).run(state)
                    count += 1
            else:
                yield state.update()
        elif start is None:
            count = end - 1
            if varq(num):
                while True:
                    yield from Eq(num, count).run(state)
                    count -= 1
            else:
                if num < end:
                    yield state.update()
                else:
                    yield state.update(valid=False)
        elif end is None:
            count = start
            if varq(num):
                while True:
                    yield from Eq(num, count).run(state)
                    count += 1
            else:
                if num >= start:
                    yield state.update()
                else:
                    yield state.update(valid=False)
        else:
            if varq(num):
                for count in range(start, end):
                    yield from Eq(num, count).run(state)
            else:
                if num >= start and num < end:
                    yield state.update()
                else:
                    yield state.update(valid=False)


class list_leno(Relation):
    """The equivalent to 'len'. We need to specify type here to make it generative.  This relation
    is key for making the rest of the list relations generative aswell.
    @param lst: A list which will have the same length as `length`
    @param length: The length of `lst`
    """
    def __init__(self, lst, length):
        super().__init__()
        self.lst = lst
        self.length = length

    def __run__(self, state):
        lst = state.reify(self.lst)
        length = state.reify(self.length)

        if varq(lst) and varq(length):
            newLength = 0
            newList = []
            while True:
                yield from Conj(Eq(length, newLength), Eq(lst, newList)).run(state)
                newList = newList + [LVar()]
                newLength += 1
        elif varq(lst):
            yield from Eq(lst, [LVar() for count in range(0,length)]).run(state)
        elif varq(length):
            yield from Eq(length, len(lst)).run(state)
        elif len(lst) == length:
            yield state
        else:
            yield state.update(valid=False)

def list_emptyo(lst):
    """This simple relation just asserts that the given `lst` is empty.
    """
    return list_leno(lst, 0)

class appendo(Relation):
    """This relation combines several python functions into one. The first and obvious is `append`,
    Given `lst` and `member` as known, it will combine them to create `lst_with_member`. Conversly
    if `lst_with_member` is known, then it can be used to pop the last value off the end of the list.
    @param lst: The base list
    @param member: a member to append to the list
    @param lst_with_member: The new list with `member` appended to the end of it.
    """
    def __init__(self, lst, member, lst_with_member):
        self.lst = lst
        self.member = member
        self.lst_with_member = lst_with_member

    def __run__(self, state):
        lst = state.reify(self.lst)
        member = state.reify(self.member)
        lst_with_member = state.reify(self.lst_with_member)

        if varq(lst) and varq(lst_with_member):
            lst_len = 0
            while True:
                with conj as lst_gen:
                    list_leno(lst, lst_len)
                    list_leno(lst_with_member, lst_len+1)
                    appendo(lst, member, lst_with_member)
                yield from lst_gen.run(state)
                lst_len += 1
        elif varq(lst) and varq(member):
            if len(lst_with_member) > 0:
                with conj as deconstruct:
                    Eq(lst, lst_with_member[0:-1])
                    Eq(member, lst_with_member[-1])
                yield from deconstruct.run(state)
            else:
                yield state.update(valid=False)
        elif varq(lst):
            if len(lst_with_member) > 0:
                with conj as var_lst:
                    Eq(member, lst_with_member[-1])
                    Eq(lst, lst_with_member[0:-1])
                yield from var_lst.run(state)
            else:
                yield state.update(valid=False)
        elif varq(lst_with_member):
            yield from Eq(lst_with_member, lst + [member]).run(state)
        elif varq(member):
            if len(lst_with_member) > 0:
                with conj as for_member:
                    Eq(lst, lst_with_member[0:-1])
                    Eq(member, lst_with_member[-1])
                yield from for_member.run(state)
            else:
                yield state.update(valid=False)
        elif len(lst_with_member) > 0:
            with conj as no_vars:
                Eq(lst_with_member[0:-1], lst)
                Eq(lst_with_member[-1], member)
            yield from no_vars.run(state)
        else:
            yield state.update(valid=False)


class indexo(Relation):
    """This combines functionality to reference an value by it's index in a list and
    the ability to get the index of one or more values in a list.  There is a one to
    one relationship between a list and it's index, so only one state will be generated
    if all arguments except the value are established.  If the index is not know then
    it will generate 2 states for every matching value in the list, one finding the
    positive index and another finding the negative index since either could match.
    @param lst: The base list
    @param value: The value to look for in the list
    @param index: The index at which the value is located
    """
    def __init__(self, lst, index, value):
        super().__init__()
        self.lst = lst
        self.value = value
        self.index = index

    def __run__(self, state):
        lst = state.reify(self.lst)
        value = state.reify(self.value)
        index = state.reify(self.index)

        if varq(lst) and varq(index):
            lst_len = 1
            while True:
                with conj as lst_gen:
                    list_leno(lst, lst_len)
                    indexo(lst, index, value)
                yield from lst_gen.run(state)
                lst_len += 1
        elif varq(value) and varq(index):
            for n in range(len(lst)):
                with conj as val_ind:
                    Eq(value, lst[n])
                    with disj:
                        Eq(index, n)
                        Eq(index, n - len(lst))
                yield from val_ind.run(state)
        elif varq(lst):
            lst_len = index + 1 if index >= 0 else -index
            while True:
                with conj as lst_gen:
                    list_leno(lst, lst_len)
                    indexo(lst, index, value)

                yield from lst_gen.run(state)
                lst_len += 1
        elif varq(value):
            if len(lst) <= index or len(lst) < -index:
                yield state.update(valid=False)
            else:
                yield from Eq(value, lst[index]).run(state)
        elif varq(index):
            for n in range(len(lst)):
                with conj as lst_gen:
                    Eq(lst[n], value)
                    with disj:
                        Eq(index, n)
                        Eq(index, n - len(lst))
                yield from lst_gen.run(state)
        else:
            if len(lst) <= index or len(lst) < -index:
                yield state.update(valid=False)
            else:
                yield from Eq(lst[index], value).run(state)

class sliceo(Relation):
    """The relation version of the python slice which will relate a list
    with a sub-list based on a start (inclusive) and end (exclusive) value.
    @param lst: The base list being sliced.
    @param start: The first value in the sublst, starts at the beginning of `lst` if `None`
    @param end: The index following the last value in the sublst, goes through the end of `lst` if `None`
    @param sublst: A sublist of lst
    """
    def __init__(self, lst, start, end, sublst):
        super().__init__()
        self.lst = lst
        self.start = start
        self.end = end
        self.sublst = sublst


    def __run__(self, state):
        lst = state.reify(self.lst)
        start = state.reify(self.start)
        end = state.reify(self.end)
        sublst = state.reify(self.sublst)

        lvar_count = varq(lst) + varq(start) + varq(end) + varq(sublst)
        if lvar_count > 2:
            with conj as full_gen:
                rangeo(start)
                rangeo(end)
                list_leno(lst, lst_len)
                sliceo(lst, start, end, sublst)
            yield from full_gen
        elif varq(lst) and (varq(start) or varq(end)):
            while True:
                lst_len = len(sublst)
                with conj as list_gen:
                    leno(lst, lst_len)
                    sliceo(lst, start, end, sublst)
                yield from list_gen
        elif varq(start) and varq(end):
            with conj as unknown_start_end:
                with disj:
                    Eq(start, None)
                    rangeo(start, None, None)
                sliceo(lst, start, end, sublst)

        elif varq(sublst) and varq(start):
            yield from (Eq(start, None) & Eq(sublst, lst[:end])).run(state)
            yield from (Eq(start, 0) & Eq(sublst, lst[start:end])).run(state)
            current_start = 1
            while True:
                yield from (Eq(start, current_start) & Eq(sublst, lst[start:end]))
                yield from (Eq(start, -current_start) & Eq(sublst, lst[start:end]))
                current_start += 1
        elif varq(sublst) and varq(end):
            yield from (Eq(end, 0) & Eq(sublst, lst[start:end])).run(state)
            yield from (Eq(end, None) & Eq(sublst, lst[start:])).run(state)
            current_end = 1
            while True:
                yield from (Eq(end, current_end) & Eq(sublst, lst[start:end]))
                yield from (Eq(end, -current_end) & Eq(sublst, lst[start:end]))
                current_end += 1
        elif varq(lst) and varq(sublst):
            sublst_len = end - start if end > start else 0
            with conj as sublst_empty:
                list_leno(sublst, sublst_len)
                sliceo(lst, start, end, sublst)
            yield from sublst_empty.run(state)
        elif varq(lst):
            if start is None:
                if end is None:
                    # If both start and end are none,
                    #  then the lst and sublst are the
                    #  same.
                    yield from Eq(lst, sublst).run(state)
                    return
                elif end >= 0:
                    # The end is a positive number, the start is
                    #  undefined, therefore the list could be the
                    #  sublist or go past the end.
                    if end < len(sublst):
                        yield state.update(valid=False)
                        return
                    else:
                        lst_len = end
                else:
                    # If we know how far from the end it is,
                    #  then we know the total length of the
                    #  list because everything before the
                    #  end is the sublst.
                    with conj as bounded_length:
                        list_leno(lst, len(sublst) + -end)
                        sliceo(lst, start, end, sublst)
                    yield from bounded_length.run(state)
                    return
            elif start >= 0:
                if end is None:
                    # Full length is known because start is where
                    #  it begins, and its end matches the end of the
                    #  sublst.
                    lst_len = start + len(sublst)
                    with conj as bounded_length:
                        list_leno(lst, len(sublst) + start)
                        sliceo(lst, start, end, sublst)
                    yield from bounded_length.run(state)
                    return
                elif end >=0:
                    # Where end is the last value from the lst in the
                    #  sublst, we know that the lst is at least that long,
                    #  but could be longer.
                    if (end - start) < len(sublst):
                        yield state.update(valid=False)
                        return
                    else:
                        lst_len = end
                else:
                    # Since we know where it starts, the interval in the middle, and
                    #  how far from the end the end of the sublst is, that means
                    #  that lst can only have one length.
                    with conj as bounded_length:
                        list_leno(lst, start + len(sublst) - end)
                        sliceo(lst, start, end, sublst)
                    yield from bounded_length.run(state)
                    return
            else:
                if end is None:
                    # The end will match the list, the position of the front
                    #  of the sublst is defined from the end, therefore the
                    #  start can't go before the front of the sublst, and
                    #  the lst can be any length that's longer than the sublst.
                    if -start < len(sublst):
                        yield state.update(valid=False)
                        return
                    else:
                        lst_len = max(len(sublst), -start)
                elif end >= 0:
                    # The start is measured from the back, the end from the beginning.
                    # Where either the start could hang off the beginning or the end
                    #  could hang off the end of `lst` and still match the sublist,
                    #  ex. ['Mad Hatter', 'March Hare', 'The Dormouse'][-1:100] == ['The Dormouse']
                    #  and ['March Hare', 'The Dormouse'][-1:100] == ['The Dormouse']
                    # Multiple lists can match, limited by the absolute value of the largest
                    #  absolute value between the start and end, so in the above example the
                    #  list could be as long as 100 elements and still return the same value
                    #  so long as the last value is 'The Dormouse'.
                    if end < len(sublst) or abs(start) < len(sublst):
                        yield state.update(valid=False)
                        return
                    else:
                        lst_len = len(sublst)
                        while lst_len <= (max(end, abs(start) + 1)):
                            with conj as lst_gen:
                                list_leno(lst, lst_len)
                                sliceo(lst, start, end, sublst)
                            yield from lst_gen.run(state)
                            lst_len += 1
                        return
                else:
                    if end <= start:
                        yield from Eq(lst, []).run(state)
                        return
                    lst_len = -start
            while True:
                with conj as lst_gen:
                    list_leno(lst, lst_len)
                    sliceo(lst, start, end, sublst)
                yield from lst_gen.run(state)
                lst_len += 1
        elif varq(sublst):
            yield from Eq(sublst, lst[start:end]).run(state)
        elif varq(start):
            front = lst[:end]
            if len(sublst) > len(front):
                yield state.update(valid=False)
            else:
                start_val_pos = end - len(sublst)
                start_val_neg = start_val_pos - len(lst)
                if start_val_pos > 0:
                    with conj as get_start:
                        with disj:
                            Eq(start, start_val_pos)
                            Eq(start, start_val_neg)
                        sliceo(lst, start, end, sublst)
                    yield from get_start.run(state)
                else:
                    with conj as get_start_zero:
                        with disj:
                            Eq(start, None)
                            Eq(start, 0)
                        sliceo(lst, start, end, sublst)
                    yield from get_start_zero.run(state)
                    start_val = -1
                    while True:
                        with conj as get_start:
                            with disj:
                                Eq(start, start_val)
                            sliceo(lst, start, end, sublst)
                        yield from get_start.run(state)
                        start_val -= 1
        elif varq(end):
            back = lst[start:]
            if len(sublst) > len(back):
                yield state.update(valid=False)
            else:
                end_val_pos = len(sublst) + start
                if end_val_pos < len(lst):
                    end_val_neg = end_val_pos - len(lst)
                    with conj as get_end:
                        with disj:
                            Eq(end, end_val_pos)
                            Eq(end, end_val_neg)
                        sliceo(lst, start, end, sublst)
                    yield from get_end.run(state)
                else:
                    with conj as get_endless:
                        Eq(end, None)
                        sliceo(lst, start, end, sublst)
                    yield from get_endless.run(state)

                    while True:
                        with conj as get_end:
                            Eq(end, end_val_pos)
                            sliceo(lst, start, end, sublst)
                        yield from get_end.run(state)
                        end_val_pos += 1
        else:
            if len(sublst) > len(lst):
                yield state.update(valid=False)
            else:
                yield from Eq(lst[start:end], sublst).run(state)
