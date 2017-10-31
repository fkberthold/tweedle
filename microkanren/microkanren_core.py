def var(c):
    return [c]

def varq(x):
    return isinstance(x, list)

def vareq(x1, x2):
    return x1[0]  == x2[0]

def walk(u, s):
    pr = varq(u) and ([(variable, value) for (variable, value) in s if (vareq(u,variable))] or [False])[0]
    if pr is not False:
        return walk(pr[1], s)
    else:
        return u

def ext_s(x, v, s):
    return ([(x, v)] + s)

mzero = []

def unit(soc):
    return [soc] + mzero

def eq(u, v):
    def eqHelp(soc):
        s = unify(u, v, soc[0])
        if s:
            return unit((s, soc[1]))
        else:
            return mzero
    return eqHelp

def unify(u, v, state):
    u = walk(u, state)
    v = walk(v, state)
    if varq(u) and varq(v) and vareq(u, v):
        return state
    elif varq(u):
        return ext_s(u, v, state)
    elif varq(v):
        return ext_s(v, u, state)
    elif isinstance(u, list) and isinstance(v, list) and u and v:
        headState = unify(u[0], v[0], state)
        if headState:
            return unify(u[1:], v[1:], headState)
        else:
            return False
    elif u == v:
        return state
    else:
        return False

def call_fresh(f):
    def call_fresh_help(soc):
        c = soc[1]
        fun = f(var(c))
        return fun((soc[0], c + 1))
    return call_fresh_help

def disj(g1, g2):
    def disj_help(soc):
        return mplus(g1(soc), g2(soc))
    return disj_help

def conj(g1, g2):
    def conj_help(soc):
        return bind(g1(soc), g2)
    return conj_help

def mplus(s1, s2):
    if s1 == []:
        return s2
    elif callable(s1):
        return (lambda: mplus(s2, s1()))
    else:
        return [s1[0]] + mplus(s1[1:], s2)

def bind(s, g):
    if s == []:
        return mzero
    elif callable(s):
        return (lambda: bind(s(), g))
    else:
        return mplus(g(s[0]), bind(s[1:], g))