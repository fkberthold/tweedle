from urkanren import *

def conso(elem, lst, elemAndLst):
    def listVarq(val):
        return isinstance(val, list) or varq(val)
    def consoHelp(soc):
        if not(listVarq(lst)) or not(listVarq(elemAndLst)):
            return mzero  # Not lists or vars
        elif not (varq(lst) or varq(elemAndLst)):
            return eq([elem] + lst, elemAndLst)  # Both are lists
        elif varq(lst) and varq(elemAndLst):
            lstIsEmpty = conj(eq(lst, []),
                            eq(elemAndLst, [elem]))
            lstHasOne = call_fresh(lambda newelem:
                        conj()
            )


def caro(lst, elem):
    def caroHelp(soc):
        if not(isinstance(lst,list) or varq(lst)):
            return mzero
        elif varq(lst):
            disj(eq(lst,[elem]),
                call_fresh(lambda nextElem:
                            conj(caro(lst,))))
        return conj(
                eq(lst)