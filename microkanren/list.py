from ukanren import *
import copy
import itertools

def emptyo(lst):
    return Eq(lst, [])

class ConstructList(Proposition):
    def __init__(self, lst, knownVarList=[], minLength=0, maxLength=None):
        self.lst = lst
        self.knownVarList = knownVarList
        self.minLength = minLength
        self.maxLength = maxLength

    def run(self, state):
        s = state.substitution
        c = state.count
        varList = copy.copy(self.knownVarList)
        lstVal = state.reify(self.lst)
        if isinstance(lstVal, list):
            if (len(lstVal) >= self.minLength) and (self.maxLength is None or len(lstVal) <= self.maxLength) and len(lstVal) >= len(self.knownVarList):
                yield from Eq(lstVal[:len(self.knownVarList)], self.knownVarList).run(state)
            else:
                return
        elif not isvar(lstVal):
            return
        elif self.maxLength is not None and len(self.knownVarList) > self.maxLength:
            return
        else:
            c = c + max(0, self.minLength - len(self.knownVarList))
            newState = state
            for n in range(state.count, c):
                (newState, newVar) = newState.var()
                varList = varList + [newVar]
            while(True):
                yield from Eq(self.lst, varList).run(newState)
                (newState, newVar) = newState.var()
                varList = varList + [newVar]

class Firsto(Proposition):
    def __init__(self, lst, first):
        self.lst = lst
        self.first = first

    def __run__(self, state):
        if not(isinstance(self.lst,list) or isvar(self.lst)):
            yield from mzero
        elif isinstance(self.lst, list):
            if(len(self.lst) == 0):
                yield from mzero
            else:
                yield from Eq(self.lst[0], self.first).run(state)
        elif isvar(self.lst):
            yield from ConstructList(self.lst, [self.first]).run(state)
        else:
            yield from mzero

class Resto(Proposition):
    def __init__(self, lst, rest):
        self.lst = lst
        self.rest = rest

    def restPairGen(self, state):
        yield from Conj(Eq(self.lst, []),
                        Eq(self.rest, [])).run(state)
        substitution = copy.copy(state.substitution)
        count = state.count
        (newState, first) = state.var()
        fullList = [first]
        while True:
            yield from Conj(Eq(self.lst, fullList),
                          Eq(self.rest, fullList[1:])).run(newState)
            (newState, newVar) = newState.var()
            fullList = fullList + [newVar]

    def __run__(self, state):
        lst_val = state.reify(self.lst)
        rest_val = state.reify(self.rest)
        if not(isinstance(lst_val, list) or isvar(lst_val)):
            yield from mzero
        elif not(isinstance(rest_val, list) or isvar(rest_val)):
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
