from microkanren.ukanren import *
from macropy.core.quotes import macros, q, u, name, ast
from macropy.core.macros import *
from macropy.core import unparse
from ast import *

macros = Macros()

@macros.decorator
def goal(tree, expand_macros, **kw):
    tree = expand_macros(tree)
    calls = []
    for stmt in tree.body:
        if isinstance(stmt, Expr):
            calls.append(stmt.value)
        elif isinstance(stmt, list):
            calls.append(stmt[0].value)
    conjGoal = q[Conj()]
    conjGoal.args = calls
    tree.body = [Return(conjGoal)]
    return tree

@macros.block
def conj(tree, args, **kw):
    target = kw.get('target')
    expand_macros = kw['expand_macros']
    tree = expand_macros(tree)
    calls = []
    for stmt in tree:
        if isinstance(stmt, Expr):
            calls.append(stmt.value)
        elif isinstance(stmt, list):
            calls.append(stmt[0].value)
    conjGoal = q[Conj()]
    conjGoal.args = calls
    if target:
        return [Assign([target], conjGoal)]
    else:
        return [Expr(conjGoal)]

@macros.block
def disj(tree, **kw):
    target = kw.get('target')
    expand_macros = kw['expand_macros']
    tree = expand_macros(tree)
    calls = []
    for stmt in tree:
        if isinstance(stmt, Expr):
            calls.append(stmt.value)
        elif isinstance(stmt, list):
            calls.append(stmt[0].value)
    disjGoal = q[Disj()]
    disjGoal.args = calls
    if target:
        return [Assign([target], disjGoal)]
    else:
        return [Expr(disjGoal)]

@macros.block
def fresh(tree, target, expand_macros, **kw):
    print("===fresh===")
    print(real_repr(tree))
    print(real_repr(target))
    tree = expand_macros(tree)
    calls = []
    for stmt in tree:
        if isinstance(stmt, Expr):
            calls.append(stmt.value)
        elif isinstance(stmt, list):
            calls.append(stmt[0].value)
    conjGoal = q[Conj()]
    conjGoal.args = calls
    if target:
        return [Assign([target], conjGoal)]
    else:
        return [Expr(conjGoal)]
