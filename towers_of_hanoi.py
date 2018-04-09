from microkanren.urconstraintkanren import *

def deep_walk(term, substitution):
    value = walk(term, substitution)
    if isinstance(value, Link):
        return Link(deep_walk(value.head, substitution), deep_walk(value.tail, substitution))
    else:
        return value

def call_fresh_x(f):
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
        newState = State(state.constraints, state.constraintFunctions, new_c)
        yield from fun(newState)
    return generate(call_fresh_help)

def run_x(f):
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
        newState = State(state.constraints, state.constraintFunctions, new_c)
        state_generator = fun(newState)
        for gen_state in state_generator:
            constraints = gen_state.constraints
            if 'eq' in constraints:
                new_constraints = {**constraints, 'eq':frozenset({(var, deep_walk(var, constraints['eq'])) for var in new_vars})}
                yield State(new_constraints, gen_state.constraintFunctions, gen_state.count)
    def run_x_help(state):
        generator = generate(call_fresh_help)(state)
        for new_state in generator:
            yield new_state.constraints.get('eq', frozenset())
    return run_x_help

def conj_x(*args):
    if len(args) <= 2:
        return conj(args[0], args[1])
    else:
        return conj(args[0], conj_x(*args[1:]))

def disj_x(*args):
    if len(args) <= 2:
        return disj(args[0], args[1])
    else:
        return disj(args[0], disj_x(*args[1:]))

def conso(head, tail, lst):
    if varq(lst):
        return call_fresh_x(lambda new_head, new_tail:
                            conj_x(eq(new_head, head),
                                   eq(new_tail, tail),
                                   eq(lst, Link(new_head, new_tail))))
    elif isinstance(lst, Link):
        return conj_x(eq(head, lst.head),
                     eq(tail, lst.tail))
    else:
        return lambda state: mzero

def lt(less, more):
#    def valsLessThan(val, lessThans):
#        newValues = set()
#        values = {lesser for (lesser, greater) in lessThans if greater == val}
#        checkedValues = set()
#        while values:
#            for lesserValue in values:
#                newValues = newValues | {lesser for (lesser, greater) in lessThans if greater == lesserValue}
#            checkedValues = checkedValues | values
#            values = newValues
#            newValues = set()
#
#    def knownLessThan(lessValue, moreValue, lessThans):
#        if not(varq(lessValue) or varq(moreValue)):
#            return lessValue < moreValue
#        elif lessValue == moreValue:
#            return False
#        else:
#
#    def ltHelp(state):
#        substitution = state.constraint.get("eq", frozenset())
#        lessThans = state.constraint.get("lt", frozenset())
#        lessValue = walk(less, substitution)
#        valuesLessThanLeast = valsLessThan()
#        moreValue = walk(more, substitution)
#
#        fails = 
    def ltWalk(term, lessThans):
        assert varq(term), "Can't walk a non-variable."
        terms = set([term])
        checkedTerms = set()
        while terms:
            newTerms = {lesser for (lesser, greater) in lessThans if greater in terms}
            checkedTerms = checkedTerms | terms
            terms = newTerms
        literals = {literal for literal in terms if not varq(literal)}
        terms = {term for term in terms if varq(term)}
        leastLiteral = min(literals) if literals else None
        return (leastLiteral, terms)

    def mtWalk(term, lessThans):
        assert varq(term), "Can't walk a non-variable."
        terms = set([term])
        checkedTerms = set()
        while terms:
            newTerms = {greater for (lesser, greater) in lessThans if lesser in terms}
            checkedTerms = checkedTerms | terms
            terms = newTerms
        literals = {literal for literal in terms if not varq(literal)}
        terms = {term for term in terms if varq(term)}
        mostLiteral = max(literals) if literals else None
        return terms

    def ltHelp(state):
        substitution = state.constraints.get("eq", frozenset())
        lessValue = walk(less, substitution)
        moreValue = walk(more, substitution)
        if not(varq(lessValue) or varq(lessValue)):
            if lessValue < moreValue:
                return state
            else:
                return mzero
        lessThans = state.constraints.get("lt", frozenset())
        if varq(lessValue):
            (leastLiteral, leastSet) = ltWalk(lessValue, lessThans)
            if not varq(moreValue):
                if moreValue <= leastLiteral:
                    return make_constraint(state, False, lt, less, more)
                else:
                    return mzero
            else:
                if moreValue in leastSet:
                    return mzero
        if varq(moreValue):
            (mostLiteral, mostSet) = mtWalk(moreValue, lessThans)
            if not varq(lessValue):
                if lessValue >= mostLiteral:
                    return make_constraint(state, False, lt, less, more)
                else:
                    return mzero
            else:
                if lessValue in mostSet:
                    return mzero
        return make_constraint(state, False, lt, less, more)
    return generate(ltHelp)

def gt(more, less):
    return lt(less, more)
