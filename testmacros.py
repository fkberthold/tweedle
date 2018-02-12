from microkanren.macro import macros, conj, goal, ast
from microkanren.ukanren import *

@goal
def equal(val1, val2, val3):
#    Eq(val1, val2)
#    Eq(val2, val3)
    return Conj(Eq(1, 2))


