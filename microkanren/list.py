from microkanren.urkanren import *
import copy
import itertools

def isListo(lst, knownVarList=[]):
    def varListHelp(state):
        s = state.substitution
        c = state.count
        varList = copy.copy(knownVarList)
        if isinstance(lst, list):
            yield state
        elif not varq(lst):
            return
        else:
            while(True):
                yield from eq(lst, varList)(State(s, c))
                varList.append(var(c))
                c += 1
    return varListHelp

def conso(elem, lst, elemAndLst):
    return conj(heado(elemAndLst, elem),
                tailo(elemAndLst, lst))

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
            return isListo(lst, [head])(state)
        else:
            return mzero
    return headoHelp

def tailo(lst, tail):
    def tailPairGen(soc):
        print("soc: " + str(soc))
        yield from conj(eq(lst, []),
                        eq(tail, []))(soc)
        (s, c) = soc
        headless = []
        head = var(c)
        headed = [head]
        c += 1
        while True:
            yield from conj(eq(lst, headed),
                            eq(tail, headless))((s, c))
            headless.append(var(c))
            headed.append(var(c))
            c += 1
    def tailoHelp(soc):
        if not(isinstance(lst, list) or varq(lst)):
            return mzero
        elif not(isinstance(tail, list) or varq(tail)):
            return mzero
        elif isinstance(lst, list):
            return eq(lst[1:], tail)(soc)
        elif isinstance(tail, list):
            return call_fresh(lambda lstHead: eq(lst, [lstHead] + tail))(soc)
        else:
            return tailPairGen(soc)
    return tailoHelp