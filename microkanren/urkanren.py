import types
import collections
import copy
import traceback
import sys
from inspect import signature

class LogicVariable(object):
    def __init__(self, identifier, name=None):
        self.id = identifier
        self.name = name

    def __eq__(self, other):
        return isinstance(other, LogicVariable) and self.id == other.id

    def __repr__(self):
        if self.name:
            return "~%s(%i)" % (self.name, self.id)
        else:
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

def var(c, name=None):
    """Var creates a Term by wrapping an integer in a list"""
    return LogicVariable(c, name)


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

def eq(left, right):
    """Returns a function that takes a state/count object and returns
        a list of new state/count objects.
       If left and right are both set terms, determines if they are the same.
           If they are, returns the state as is.
           If they are not, then returns an empty state.
       If left or right is a variable, then asserts they are equal and adds it to,
          the state. If they are not equal, then returns an empty state."""
    def eqHelp(state):
        unified = unify(left, right, state.substitution)
        if isinstance(unified, dict):
            return unit(State(unified, state.count))
        else:
            return mzero
    return generate(eqHelp)

def unify(left, right, substitution):
    """Given a pair of terms determines if they can be equivalent.
        If they are both the same established value, returns the substitution.
        If one or the other value is unknown, then updates the substitution with
            the unkown value being set to the known value.
        If they can't be unified then returns False."""
    left = walk(left, substitution)
    right = walk(right, substitution)
    if varq(left) and varq(right) and vareq(left, right):
        return substitution
    elif varq(left):
        return ext_s(left, right, substitution)
    elif varq(right):
        return ext_s(right, left, substitution)
    elif isinstance(left, list) and isinstance(right, list) and len(left) == len(right) and len(left) > 0:
        headSub = unify(left[0], right[0], substitution)
        if headSub is not False:
            return unify(left[1:], right[1:], headSub)
        else:
            return False
    elif left == right:
        return substitution
    else:
        return False

def call_fresh(f):
    """Takes a *-arity function which returns a list of states.  It assigns the given argument
        an unassigned term.  It then returns a function that takes a state and returns a list of
        states."""
    def call_fresh_help(state):
        c = state.count
        params = signature(f).parameters
        arg_count = len(params)
        new_c = c + arg_count
        new_vars = [var(number, name) for (number, name) in zip(range(c, new_c), params)]
        fun = f(*new_vars)
        newState = State(state.substitution, new_c)
        yield from fun(newState)
    return generate(call_fresh_help)

def disj(*gs):
    """Take multiple relations. For each one that evaluates true, concatenate and return
        it's results."""
    def disj_help(state):
        yield from mplus(*[g(state) for g in gs])
    return generate(disj_help)

def conj(*gs):
    """Take two relations. Determine the result if both are true."""
    def conj_help(state):
        yield from bind(*gs)(state)
    return conj_help

def generate(fun):
    """If `state` is a single state, applies fun to it, if it is a generator,
       then applies fun across the generator and yields for each result.

       If fun returns a single state, returns a generator that yields the one
       state, if it returns a generator, then will yield over that genrator."""
    def generate_help(state):
        if isinstance(state, types.GeneratorType):
            for genState in state:
                result = fun(genState)
                if isinstance(result, State):
                    yield result
                else:
                    yield from result
        else:
            result = fun(state)
            if isinstance(result, State):
                yield result
            else:
                yield from result
    return generate_help

def mplus(*states):
    if len(states) == 0:
        return empty
    else:
        stateStreams = states
        newStreams = []
        while stateStreams:
            for stateStream in stateStreams:
                try:
                    result = stateStream.__next__()
                    if isinstance(result, State):
                        yield result
                    else:
                        newStreams.append(result)
                    newStreams.append(stateStream)
                except StopIteration:
                    pass
            stateStreams=newStreams
            newStreams=[]

def bind(*goals):
    def bind_help(states):
        if len(goals) == 0:
            yield from states
        elif len(goals) == 1:
            yield from goals[0](states)
        else:
            stateStreams = []
            newStreams = []
            for state in goals[0](states):
                stateStreams = [bind(*goals[1:])(unit(state))] + stateStreams
                for stateStream in stateStreams:
                    try:
                        result = stateStream.__next__()
                        if isinstance(result, State):
                            yield result
                        else:
                            newStreams.append(result)
                        newStreams.append(stateStream)
                    except StopIteration:
                        pass
                stateStreams = newStreams
                newStreams = []
            while stateStreams:
                for stateStream in stateStreams:
                    try:
                        result = stateStream.__next__()
                        if isinstance(result, State):
                            yield result
                        else:
                            newStreams.append(result)
                        newStreams.append(stateStream)
                    except StopIteration:
                        pass
                stateStreams = newStreams
                newStreams = []

    return generate(bind_help)
