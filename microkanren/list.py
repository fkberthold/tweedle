from microkanren.urkanren import *
import copy
import itertools

def emptyo(lst):
    return eq(lst, [])

def constructList(lst, knownVarList=[], minLength=0, maxLength=None):
    def varListHelp(state):
        s = state.substitution
        c = state.count
        varList = copy.copy(knownVarList)
        lstVal = walk(lst, s)
        if isinstance(lstVal, list):
            if (len(lstVal) >= minLength) and (maxLength is None or len(lstVal) <= maxLength) and len(lstVal) >= len(knownVarList):
                yield from eq(lstVal[:len(knownVarList)], knownVarList)(state)
            else:
                return
        elif not varq(lstVal):
            return
        elif maxLength is not None and len(knownVarList) > maxLength:
            return
        else:
            c = c + max(0, minLength - len(knownVarList))
            varList = varList + [var(n) for n in range(state.count, c)]
            while(True):
                yield from eq(lst, varList)(State(s, c))
                varList.append(var(c))
                c += 1
    return generate(varListHelp)

def firsto(lst, first):
    def firstoHelp(state):
        if not(isinstance(lst,list) or varq(lst)):
            return mzero
        elif isinstance(lst, list):
            if(len(lst) == 0):
                return mzero
            else:
                return eq(lst[0], first)(state)
        elif varq(lst):
            return constructList(lst, [first])(state)
        else:
            return mzero
    return generate(firstoHelp)

def resto(lst, rest):
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
    def restoHelp(state):
        lst_val = walk(lst, state.substitution)
        rest_val = walk(rest, state.substitution)
        if not(isinstance(lst_val, list) or varq(lst_val)):
            return mzero
        elif not(isinstance(rest_val, list) or varq(rest_val)):
            return mzero
        elif isinstance(lst_val, list):
            return eq(lst_val[1:], rest)(state)
        elif isinstance(rest_val, list):
            return call_fresh(lambda lstFirst: eq(lst, [lstFirst] + rest_val))(state)
        else:
            return restPairGen(state)
    return generate(restoHelp)

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
