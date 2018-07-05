from microkanren.ukanren import *
from macropy.core.quotes import macros, q, u, name, ast
from macropy.core.macros import *
from ast import *

macros = Macros()

@macros.decorator
def goal(tree, expand_macros, **kw):
    tree = expand_macros(tree)
    calls = []
    for stmt in tree.body:
        if isinstance(stmt, Expr) and isinstance(stmt.value, Call):
            calls.append(stmt.value)
        elif isinstance(stmt, list):
            calls.append(stmt[0].value)
    conjGoal = q[Conj()]
    conjGoal.args = calls
    tree.body = [Return(conjGoal)]
    return tree

def blockfor(goal, tree, args, target, expand_macros):
    tree = expand_macros(tree)
    calls = []
    for stmt in tree:
        if isinstance(stmt, Expr) and isinstance(stmt.value, Call):
            calls.append(stmt.value)
        elif isinstance(stmt, list):
            calls.append(stmt[0].value)
    goal.args = calls
    if target:
        return [Assign([target], goal)]
    elif args:
        funArgs = arguments([arg(a.id, None) for a in args], None, [], [], None, [])
        fun = Lambda(funArgs, goal)
        fresh = q[Fresh()]
        fresh.args = [fun]
        return [Expr(fresh)]
    else:
        return [Expr(goal)]


@macros.block
def conj(tree, **kw):
    target = kw.get('target')
    args = kw.get('args')
    expand_macros = kw['expand_macros']
    return blockfor(q[Conj()], tree, args, target, expand_macros)

@macros.block
def disj(tree, **kw):
    target = kw.get('target')
    args = kw.get('args')
    expand_macros = kw['expand_macros']
    return blockfor(q[Disj()], tree, args, target, expand_macros)


@macros.block
def call(tree, **kw):
    target = kw.get('target')
    args = kw.get('args')
    expand_macros = kw['expand_macros']
    tree = expand_macros(tree)
    calls = []
    for stmt in tree:
        if isinstance(stmt, Expr) and isinstance(stmt.value, Call):
            calls.append(stmt.value)
        elif isinstance(stmt, list):
            calls.append(stmt[0].value)
    goal = q[Conj()]
    goal.args = calls
    if target:
        return [Assign([target], goal)]
    elif args:
        funArgs = arguments([arg(a.id, None) for a in args], None, [], [], None, [])
        fun = Lambda(funArgs, goal)
        fresh = q[Call()]
        fresh.args = [fun]
        return [Expr(fresh)]
    else:
        return [Expr(goal)]
