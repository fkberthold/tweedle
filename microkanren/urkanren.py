import types
from inspect import signature

class LogicVariable(object):
    def __init__(self, identifier):
        self.id = identifier

    def __eq__(self, other):
        return isinstance(other, LogicVariable) and self.id == other.id

    def __repr__(self):
        return "~%i" % self.id

    def __hash__(self):
        return self.id

class State(object):
    def __init__(self, substitution={}, count=0):
        assert count >= 0
        assert len(substitution) <= count
        self.count = count
        self.substitution = substitution

    def __hash__(self):
        return hash((self.count, tuple(self.substitution.keys()), tuple(self.substitution.values())))

    def __eq__(self, other):
        assert isinstance(other, State)
        return self.count == other.count and self.substitution == other.substitution

    def __repr__(self):
        subs = "\n".join(["  %s: %s" % (repr(key), repr(self.substitution[key])) for key in self.substitution])
        return "\nCount: %i\nSubstitutions:\n%s" % (self.count, subs)

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

def walk(term, substitution):
    """Walk through the given substitution.
        If the term is not a variable, return it,
        If the term is a variable and the first value found is not a variable, return it.
        If the first value found is a variable, repeat walking on that variable."""
    if isinstance(term, LogicVariable):
        value = substitution.get(term, term)
        if isinstance(value, LogicVariable) and value != term:
            return walk(value, substitution)
        else:
            return value
    else:
        return term

def ext_s(variable, value, substitution):
    """Add a value v to variable x for the given substitution s"""
    new = {variable:value}
    return {**substitution, **new}

# The state when there is a contradiction in terms.
mzero = iter([])

def unit(state):
    """Don't change anything"""
    yield state

def eq(u, v):
    """Returns a function that takes a state/count object and returns
        a list of new state/count objects.
       If u and v are both set terms, determines if they are the same.
           If they are, returns the state as is.
           If they are not, then returns an empty state.
       If u or v is a variable, then asserts they are equal and adds it to,
          the state. If they are not equal, then returns an empty state."""
    def eqHelp(state):
        s = unify(u, v, state.substitution)
        if s:
            return unit(State(s, state.count))
        else:
            return mzero
    return eqHelp

def unify(u, v, substitution):
    """Given a pair of terms determines if they can be equivalent.
        If they are both the same established value, returns the substitution.
        If one or the other value is unknown, then updates the substitution with
            the unkown value being set to the known value.
        If they can't be unified then returns False."""
    u = walk(u, substitution)
    v = walk(v, substitution)
    if varq(u) and varq(v) and vareq(u, v):
        return substitution
    elif varq(u):
        return ext_s(u, v, substitution)
    elif varq(v):
        return ext_s(v, u, substitution)
    elif isinstance(u, list) and isinstance(v, list) and u and v:
        headSub = unify(u[0], v[0], substitution)
        if headSub is not False:
            return unify(u[1:], v[1:], headSub)
        else:
            return False
    elif u == v:
        return substitution
    else:
        return False

def call_fresh(f):
    """Takes a *-arity function which returns a list of states.  It assigns the given argument
        an unassigned term.  It then returns a function that takes a state and returns a list of
        states."""
    def call_fresh_help(state):
        c = state.count
        arg_count = len(signature(f).parameters)
        new_c = c + arg_count
        new_vars = [var(n) for n in range(c, new_c)]
        fun = f(*new_vars)
        newState = State(state.substitution, new_c)
        return fun(newState)
    return call_fresh_help

def disj(*gs):
    """Take multiple relations. For each one that evaluates true, concatenate and return
        it's results."""
    def disj_help(state):
        yield from mplus((g(state) for g in gs))
    return disj_help

def conj(*gs):
    """Take two relations. Determine the result if both are true."""
    def conj_help(state):
        return bind(gs[0](state), *gs[1:])
    return conj_help

def mplus(*states):
    if len(states) == 0:
        return
    else:
        try:
            state0 = states[0]
            srest = states[1:]
            goal = state0.__next__()
            yield from goal
            newOrder = srest + (state0,)
            yield from mplus(*newOrder)
        except StopIteration:
            yield from mplus(*srest)


def bind(states, *g):
    if len(g) == 0:
        if isinstance(states, types.GeneratorType):
            yield from states
        else:
            yield states
    else:
        if isinstance(states, types.GeneratorType):
            for goalGen in states:
                for goal in g[0](goalGen):
                    yield from bind(goal, *g[1:])
        else:
            for goal in g[0](states):
                yield from bind(goal, *g[1:])
