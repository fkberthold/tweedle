from microkanren.urkanren import *
import copy
import itertools

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

def heado(lst, head):
    def headoHelp(state):
        if not(isinstance(lst,list) or varq(lst)):
            return mzero
        elif isinstance(lst, list):
            if(len(lst) == 0):
                return mzero
            else:
                return eq(lst[0], head)(state)
        elif varq(lst):
            return constructList(lst, [head])(state)
        else:
            return mzero
    return generate(headoHelp)

def tailo(lst, tail):
    def tailPairGen(state):
        yield from conj(eq(lst, []),
                        eq(tail, []))(state)
        substitution = state.substitution
        count = state.count
        headless = []
        head = var(count)
        headed = [head]
        count += 1
        while True:
            yield conj(eq(lst, headed),
                       eq(tail, headless))(State(substitution, count))
            headless.append(var(count))
            headed.append(var(count))
            count += 1
    def tailoHelp(state):
        lst_val = walk(lst, state.substitution)
        tail_val = walk(tail, state.substitution)
        if not(isinstance(lst_val, list) or varq(lst_val)):
            return mzero
        elif not(isinstance(tail_val, list) or varq(tail_val)):
            return mzero
        elif isinstance(lst_val, list):
            return eq(lst_val[1:], tail)(state)
        elif isinstance(tail_val, list):
            return call_fresh(lambda lstHead: eq(lst, [lstHead] + tail_val))(state)
        else:
            return tailPairGen(state)
    return generate(tailoHelp)

def conso(elem, lst, elemAndLst):
    return conj(heado(elemAndLst, elem),
                tailo(elemAndLst, lst))

def membero(elem, lst):
    isHead = call_fresh(lambda head:\
                              conj(eq(elem, head),\
                                   heado(lst, head)))
    isInTail = call_fresh(lambda tail:\
                                 conj(membero(elem, tail),
                                      tailo(lst, tail)))
    return disj(isHead, isInTail)

def appendo(list1, list2, listCombined):
    def appendoHelp(state):
        allEmpty = conj(eq(list1, []), eq(list2, []), eq(listCombined, []))
        list1Empty = call_fresh(lambda head, tail: \
                                      conj(eq(list1, []), \
                                           eq(list2, listCombined), \
                                           conso(head, tail, listCombined)))
        list2Empty = call_fresh(lambda head, tail: \
                                      conj(eq(list2, []), \
                                           eq(list1, listCombined), \
                                           conso(head, tail, listCombined)))
        recurse = call_fresh(lambda head, ltail, ctail: \
                                       conj(conso(head, ltail, list1), \
                                            conso(head, ctail, listCombined), \
                                            appendo(ltail, list2, ctail)))
        return disj(allEmpty, list1Empty, list2Empty, recurse)(state)
    return generate(appendoHelp)
