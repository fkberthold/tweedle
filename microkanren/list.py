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

def Resto(lst, rest):
    def __init__(self, lst, rest):
        self.lst = lst
        self.rest = rest

    def restPairGen(state):
        yield from conj(eq(lst, []),
                        eq(rest, []))(state)
        substitution = state.substitution
        count = state.count
        headless = []
        first = var(count)
        headed = [first]
        count += 1
        while True:
            yield conj(eq(lst, headed),
                       eq(rest, headless))(State(substitution, count))
            headless.append(var(count))
            headed.append(var(count))
            count += 1

    def __run__(state):
        lst_val = state.reify(lst)
        rest_val = state.reify(rest)
        if not(isinstance(lst_val, list) or isvar(lst_val)):
            return mzero
        elif not(isinstance(rest_val, list) or isvar(rest_val)):
            return mzero
        elif isinstance(lst_val, list):
            return Eq(lst_val[1:], rest).run(state)
        elif isinstance(rest_val, list):
            return Fresh(lambda lstFirst: Eq(lst, [lstFirst] + rest_val)).run(state)
        else:
            return restPairGen(state)

def conso(elem, lst, elemAndLst):
    return conj(firsto(elemAndLst, elem),
                resto(elemAndLst, lst))

def membero(elem, lst):
    isFirst  = firsto(lst, elem)
    isInRest = call_fresh(lambda first, rest:\
                                 conj(resto(lst, rest),\
                                      firsto(lst, first),\
                                      membero(elem, rest)))
    return disj(isFirst, isInRest)

def appendo(list1, list2, listCombined):
    def appendoHelp(state):
        allEmpty = conj(eq(list1, []), eq(list2, []), eq(listCombined, []))
        list1Empty = call_fresh(lambda first, rest: \
                                      conj(eq(list1, []), \
                                           eq(list2, listCombined), \
                                           conso(first, rest, listCombined)))
        list2Empty = call_fresh(lambda first, rest: \
                                      conj(eq(list2, []), \
                                           eq(list1, listCombined), \
                                           conso(first, rest, listCombined)))
        recurse = call_fresh(lambda first, lrest, crest: \
                                       conj(conso(first, lrest, list1), \
                                            conso(first, crest, listCombined), \
                                            appendo(lrest, list2, crest)))
        return disj(allEmpty, list1Empty, list2Empty, recurse)(state)
    return generate(appendoHelp)
