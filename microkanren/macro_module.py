from macropy.core.macros import *
from macropy.core import unparse

macros = Macros()

@macros.expr
def expand(tree, **kw):
    print("===I'm an expression===")
    print(tree)
    print(real_repr(tree))
    print(unparse(tree))
    return tree


@macros.block
def conj(tree, **kw):
    print("===I'm a block===")
    print(real_repr(tree))
    return tree

def Fresh(object):
    def __init__(self, function):
        self.function = function

class Conj(object):
    def __init__(self, goals):
        self.goals = goals

    def __repr__(self):
        print goals

@macros.decorator
def goal(tree, **kw):
    print("===I'm a decorator===")
    print(tree.name)
    print(real_repr(tree.args))
    print(real_repr(tree.body))
#    print(real_repr(tree))
    return tree
