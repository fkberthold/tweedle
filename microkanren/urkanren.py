

class LogicVariable():
    def __init__(self, identifier):
        self.id = identifier

def var(c):
    """Var creates a Term by wrapping an integer in a list"""
    return LogicVariable(c)

def varq(x):
    """Determine if a value is a var"""
    return isinstance(x, LogicVariable)

def vareq(x1, x2):
    """Determine if to vars are equal. This does not check if
    they're values are the same, but if they are exactly the same
    pointer."""
    return x1.id  == x2.id

def walk(term, state):
    """Walk through the given state.
        If the term is not a variable, return it,
        If the term is a variable and the first value found is not a variable, return it.
        If the first value found is a variable, repeat walking on that variable."""
    pr = varq(term) and ([(variable, value) for (variable, value) in state if (vareq(term,variable))] or [False])[0]
    if pr is not False:
        return walk(pr[1], state)
    else:
        return term

def ext_s(variable, value, state):
    """Add a value v to variable x for the given state s"""
    return ([(variable, value)] + state)

mzero = []

def unit(soc):
    """Don't change anything"""
    return [soc] + mzero

def eq(u, v):
    """Returns a function that takes a state/count object and returns
        a list of new state/count objects.
       If u and v are both set terms, determines if they are the same.
           If they are, returns the state as is.
           If they are not, then returns an empty state.
       If u or v is a variable, then asserts they are equal and adds it to,
          the state. If they are not equal, then returns an empty state."""
    def eqHelp(soc):
        s = unify(u, v, soc[0])
        if s:
            return unit((s, soc[1]))
        else:
            return mzero
    return eqHelp

def unify(u, v, state):
    """Given a pair of terms determines if they can be equivalent.
        If they are both the same established value, returns the state.
        If one or the other value is unknown, then updates the state with
            the unkown value being set to the known value.
        If they can't be unified then returns False."""
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
    """Takes a 1-arity function which returns a list of states.  It assigns the given argument
        an unassigned term.  It then returns a function that takes a state and returns a list of
        states."""
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