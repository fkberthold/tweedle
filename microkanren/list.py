from microkanren.ukanren import *
import copy
import itertools

def emptyo(lst):
    return Eq(lst, [])

class ConstructList(Proposition):
    def __init__(self, lst, knownVarList=[], minLength=0, maxLength=None):
        super().__init__()
        self.lst = lst
        self.knownVarList = knownVarList
        self.minLength = minLength
        self.maxLength = maxLength

    def run(self, state):
        s = state.substitution
        c = state.count
        varList = self.knownVarList
        lstVal = state.reify(self.lst)
        if isinstance(lstVal, list):
            if (len(lstVal) >= self.minLength) and (self.maxLength is None or len(lstVal) <= self.maxLength) and len(lstVal) >= len(self.knownVarList):
                yield from Eq(lstVal[:len(self.knownVarList)], self.knownVarList).run(state)
            else:
                return
        elif not varq(lstVal):
            return
        elif self.maxLength is not None and len(self.knownVarList) > self.maxLength:
            return
        else:
            (newState, varList) = state.vars(max(0, self.minLength - len(self.knownVarList)))
            while(True):
                yield from Eq(self.lst, varList).run(newState)
                (newState, newVar) = newState.var()
                varList = varList + [newVar]

class Firsto(Proposition):
    def __init__(self, lst, first):
        super().__init__()
        self.lst = lst
        self.first = first

    def __prerun__(self, state):
        lst = state.reify(self.lst)
        first = state.reify(self.first)
        if not(isinstance(lst,list) or varq(lst)):
            return state.update(valid=False)
        elif isinstance(lst, list):
            if(len(lst) == 0):
                return state.update(valid=False)
            else:
                return Eq(lst[0], first).prerun(state)
        elif varq(lst):
            return state
        else:
            return state.update(valid=False)

    def __run__(self, state):
        lst = state.reify(self.lst)
        first = state.reify(self.first)
        if not(isinstance(lst,list) or varq(lst)):
            yield from mzero
        elif isinstance(lst, list):
            if(len(lst) == 0):
                yield from mzero
            else:
                yield from Eq(lst[0], first).run(state)
        elif varq(self.lst):
            yield from ConstructList(lst, [first]).run(state)
        else:
            yield from mzero

class Resto(Proposition):
    def __init__(self, lst, rest):
        super().__init__()
        self.lst = lst
        self.rest = rest

    def restPairGen(self, state):
        yield from Conj(Eq(self.lst, []),
                        Eq(self.rest, [])).run(state)
        (newState, first) = state.var()
        fullList = [first]
        while True:
            yield from Conj(Eq(self.lst, fullList),
                          Eq(self.rest, fullList[1:])).run(newState)
            (newState, newVar) = newState.var()
            fullList = fullList + [newVar]

    def __prerun__(self, state):
        lst = state.reify(self.lst)
        rest = state.reify(self.rest)
        if not(isinstance(lst, list) or varq(lst)):
            return state.update(valid=False)
        elif not(isinstance(rest, list) or varq(rest)):
            return state.update(valid=False)
        elif isinstance(lst, list):
            return Eq(lst[1:], self.rest).prerun(state)
        elif isinstance(rest, list):
            return Fresh(lambda lstFirst: Eq(self.lst, [lstFirst] + rest_val)).prerun(state)
        else:
            return state

    def __run__(self, state):
        lst_val = state.reify(self.lst)
        rest_val = state.reify(self.rest)
        if not(isinstance(lst_val, list) or varq(lst_val)):
            yield from mzero
        elif not(isinstance(rest_val, list) or varq(rest_val)):
            yield from mzero
        elif isinstance(lst_val, list):
            yield from Eq(lst_val[1:], self.rest).run(state)
        elif isinstance(rest_val, list):
            yield from Fresh(lambda lstFirst: Eq(self.lst, [lstFirst] + rest_val)).run(state)
        else:
            yield from self.restPairGen(state)

def conso(elem, lst, elemAndLst):
    return Conj(Resto(elemAndLst, lst),
               Firsto(elemAndLst, elem))

def membero(elem, lst):
    isFirst  = Firsto(lst, elem)
    isInRest = Fresh(lambda first, rest:\
                                 Conj(Resto(lst, rest),\
                                      Firsto(lst, first),\
                                      membero(elem, rest)))
    return Disj(isFirst, isInRest)

def appendo(list1, list2, listCombined):
    allEmpty = Conj(Eq(list1, []), Eq(list2, []), Eq(listCombined, []))
    list1Empty = Fresh(lambda first, rest: \
                                      Conj(Eq(list1, []), \
                                           Eq(list2, listCombined), \
                                           conso(first, rest, listCombined)))
    list2Empty = Fresh(lambda first, rest: \
                                      Conj(Eq(list2, []), \
                                           Eq(list1, listCombined), \
                                           conso(first, rest, listCombined)))
    recurse = Fresh(lambda first, lrest, crest: \
                                       Conj(conso(first, lrest, list1), \
                                            conso(first, crest, listCombined), \
                                            appendo(lrest, list2, crest)))
    return Disj(allEmpty, list1Empty, list2Empty, recurse)
