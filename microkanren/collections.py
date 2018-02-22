from microkanren.ukanren import *
import copy
import itertools

def emptyo(lst):
    return Eq(lst, [])

class ConstructList(Relation):
    def __init__(self, lst, knownVarList=[], minLength=0, maxLength=None):
        super().__init__()
        self.lst = lst
        self.knownVarList = knownVarList
        self.minLength = minLength
        self.maxLength = maxLength

    def score(self, state, accumulator=0):
        return 100

    def __run__(self, state):
        s = state.substitution
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
            varList = varList + lvars(max(0, self.minLength - len(self.knownVarList)))
            while(True):
                yield from Eq(self.lst, varList).run(state)
                newVar = LVar()
                varList = varList + [newVar]

class firsto(Relation):
    def __init__(self, lst, first):
        super().__init__()
        self.lst = lst
        self.first = first

    def score(self, state, accumulator=0):
        if varq(state.reify(self.lst)):
            return MAX_SCORE
        else:
            return 1

    def __repr__(self):
        return "first(%s, %s)" % (str(self.lst), str(self.first))

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

class resto(Relation):
    def __init__(self, lst, rest):
        super().__init__()
        self.lst = lst
        self.rest = rest

    def __repr__(self):
        return "rest(%s, %s)" % (str(self.lst), str(self.rest))

    def score(self, state, accumulator=0):
        lst = state.reify(self.lst)
        rest = state.reify(self.rest)
        if not varq(lst):
            return len(lst)
        elif not varq(rest):
            return len(rest)
        else:
            return MAX_SCORE

    def restPairGen(self, state):
        yield from (Eq(self.lst, []) & Eq(self.rest, [])).run(state)
        first = LVar()
        fullList = [first]
        while True:
            yield from (Eq(self.lst, fullList) & Eq(self.rest, fullList[1:])).run(state)
            newVar = LVar()
            fullList = fullList + [newVar]

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
    return resto(elemAndLst, lst) & firsto(elemAndLst, elem)

def membero(elem, lst):
    isFirst  = firsto(lst, elem)
    isInRest = Fresh(lambda first, rest:\
                                 resto(lst, rest) & firsto(lst, first) & membero(elem, rest))
    return isFirst | isInRest

def appendo(list1, list2, listCombined):
    allEmpty = Eq(list1, []) & Eq(list2, []) & Eq(listCombined, [])
    list1Empty = Fresh(lambda first, rest: \
                             Eq(list1, []) & Eq(list2, listCombined) & conso(first, rest, listCombined))
    list2Empty = Fresh(lambda first, rest:
                             Eq(list2, []) & Eq(list1, listCombined) & conso(first, rest, listCombined))
    recurse = Fresh(lambda first, lrest, crest: \
                             conso(first, lrest, list1) & conso(first, crest, listCombined) & appendo(lrest, list2, crest))
    return allEmpty | list1Empty | list2Empty | recurse