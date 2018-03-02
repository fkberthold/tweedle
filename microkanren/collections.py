from microkanren.ukanren import *
import copy
import itertools
from microkanren.macro import macros, conj, disj, goal, call
import time

class list_leno(Relation):
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
    return list_leno(lst, 0)

class indexo(Relation):
    def __init__(self, lst, value, index):
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
                    indexo(lst, value, index)
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
                    indexo(lst, value, index)

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
