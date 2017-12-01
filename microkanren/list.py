from urkanren import *
import copy
import itertools

def isListo(lst, knownVarList=[]):
    def varListHelp(soc):
        s = soc[0]
        c = soc[1]
        varList = copy.copy(knownVarList)
        if isinstance(lst, list):
            yield soc
        elif not varq(lst):
            return
        else:
            while(True):
                yield from eq(lst, varList)((s, c))
                varList.append(var(c))
                c += 1
    return varListHelp
"""
def conso(elem, lst, elemAndLst):
    def listVarq(val):
        return isinstance(val, list) or varq(val)
    def consoHelp(soc):
        if not(listVarq(lst)) or not(listVarq(elemAndLst)):
            return mzero  # Not lists or vars
        elif not (varq(lst) or varq(elemAndLst)):
            return eq([elem] + lst, elemAndLst)(soc)  # Both are lists
        elif varq(lst) and varq(elemAndLst):
            return conj(isListo(lst),
                        isListo(elemAndLst),



            lstIsEmpty = conj(eq(lst, []),
                            eq(elemAndLst, [elem]))
            construction = call_fresh(lambda head, tail:
                                    conj(conso(head, tail, elemAndLst),
                                         eq(elem, head),
                                         eq(lst, tail)))
            return disj(lstIsEmpty, construction)(soc)
        elif varq(lst):
            return conj(eq(elem, elemAndLst[0]),
                        eq(lst, elemAndLst[1:]))(soc)
        else:
            return eq([elem] + lst, elemAndLst)(soc)
    return consoHelp
"""

def heado(lst, head):
    def headoHelp(soc):
        if not(isinstance(lst,list) or varq(lst)):
            return mzero
        elif isinstance(lst, list):
            if(len(lst) == 0):
                return mzero
            else:
                return eq(lst[0], head)(soc)
        elif varq(lst):
            return isListo(lst, [head])(soc)
        else:
            return mzero
    return headoHelp

def tailo(lst, tail):
    def tailPairGen(soc):
        c = soc[1]
        s = soc[0]
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