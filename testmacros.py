from microkanren.macro import macros, conj, disj, goal
from microkanren.ukanren import *
from microkanren.list import *

@goal
def myCons(head, tail, lst):
    firsto(lst, head)
    resto(lst, tail)

@goal
def numb(n1, n2):
    with disj:
        with conj:
            Eq(n1, 3)
            Eq(n1, n2)
        with conj:
            Eq(n1, 5)
            Eq(n2, 8)

with conj(a,b), conj as numCase:
    Eq(a, 3)
    numb(a, b)

for st in numCase.run():
    print("== State ==")
    print(st)


