from microkanren.ukanren import *
from macropy.core.quotes import macros, q, u, name, ast
from macropy.core.macros import *
from macropy.core import unparse
from ast import *

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

@macros.decorator
def goal(tree, **kw):
    print("===I'm a decorator===")
    print(tree.name)
    print("Args: " + real_repr(tree.args))
    print("Body: " + real_repr(tree.body))
    print("Tree: " + real_repr(tree))
    body = tree.body
#    tree.body = []
    bodyGoal = Return(q[Conj(*(ast[tree.body]))])
    print(real_repr(bodyGoal))
    return tree


def nothing():
    print("***ARGS***")
    args = [arg(a.arg, None) for a in tree.args.args]
    print("ARGS: " + real_repr(args))
#    print("\n\n\nEmpty Lambda: " + real_repr(fun))
#    print("\n\n\nConj: " + real_repr(q[lambda x, y: Conj(x, y)]))
#    fun = q[lambda: Conj(*u[tree.body])]
#    print("fun: " + real_repr(fun))
#    print(real_repr(q[Fresh(lambda: Conj(*tree.body))]))
    fr = q[Fresh(u[fun])]
    print("Fresh: " + real_repr(fr))
    print(fr)
    return fr
#    print(real_repr(tree))
#    return q[Fresh(lambda *(tree.args): Conj(*tree.body))]

