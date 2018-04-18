from microkanren.urconstraintkanren import *

def deep_walk(term, substitution):
    value = walk(term, substitution)
    if isinstance(value, Link):
        return Link(deep_walk(value.head, substitution),
                    deep_walk(value.tail, substitution))
    else:
        return value

def call_fresh_x(f):
    """Takes a *-arity function which returns a list of states.  It assigns the
    given argument an unassigned term.  It then returns a function that takes a
    state and returns a list of states."""
    def call_fresh_help(state):
        c = state.count
        params = signature(f).parameters
        arg_count = len(params)
        new_c = c + arg_count
        ids_and_params = zip(range(c, new_c), params)
        new_vars = [var(number, name) for (number, name) in ids_and_params]
        fun = f(*new_vars)
        newState = State(state.constraints, state.constraintFunctions, new_c)
        yield from fun(newState)
    return generate(call_fresh_help)

def run_x(f):
    """Takes a *-arity function which returns a list of states.  It assigns the
    given argument an unassigned term.  It then returns a function that takes a
    state and returns a list of states."""
    def call_fresh_help(state):
        c = state.count
        params = signature(f).parameters
        arg_count = len(params)
        new_c = c + arg_count
        ids_and_params = zip(range(c, new_c), params)
        new_vars = [var(number, name) for (number, name) in ids_and_params]
        fun = f(*new_vars)
        newState = State(state.constraints, state.constraintFunctions, new_c)
        state_generator = fun(newState)
        for gen_state in state_generator:
            constraints = gen_state.constraints
            constraintFunctions = gen_state.constraintFunctions
            count = gen_state.count
            if 'eq' in constraints:
                old_eq = constraints['eq']
                new_eq = {(var, deep_walk(var, old_eq)) for var in new_vars}
                new_constraints = {**constraints, 'eq': frozenset(new_eq)}
                yield State(new_constraints, constraintFunctions, count)
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

def emptyo(lst):
    return eq(lst, Link())

def not_emptyo(lst):
    return neq(lst, Link())

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
    def ltWalk(term, lessThans):
        assert varq(term), "Can't walk a non-variable."
        terms = set([term])
        checkedTerms = set()
        mostPlus = 1 # When calculating how much more anything else must be to
                     #  be valid, each iteration deeper we go in terms, then the
                     #  amount added must be one larger too.
        while terms:
            newTerms = {lesser if varq(lesser) else lesser + mostPlus for
                        (lesser, greater) in lessThans if greater in terms}
            checkedTerms = checkedTerms | terms
            terms = newTerms
            mostPlus += 1
        literals = {literal for literal in checkedTerms if not varq(literal)}
        terms = {term for term in checkedTerms if varq(term)}
        # You want the maximum literal value because any value that is more than
        #  term must by definition be larger than the highest number it could be
        #  greater than plus one.
        mostLiteral = max(literals) if literals else None
        return (mostLiteral, terms)

    def mtWalk(term, lessThans):
        assert varq(term), "Can't walk a non-variable."
        terms = set([term])
        checkedTerms = set()
        leastMinus = 1
        while terms:
            newTerms = {greater if varq(greater) else greater - leastMinus for
                        (lesser, greater) in lessThans if lesser in terms}
            checkedTerms = checkedTerms | terms
            terms = newTerms
            leastMinus += 1
        literals = {literal for literal in checkedTerms if not varq(literal)}
        terms = {term for term in checkedTerms if varq(term)}
        # See above for why least
        leastLiteral = min(literals) if literals else None
        return (leastLiteral, terms)

    def ltHelp(state):
        substitution = state.constraints.get("eq", frozenset())
        lessValue = walk(less, substitution)
        moreValue = walk(more, substitution)
        if not(varq(lessValue) or varq(moreValue)):
            if lessValue < moreValue:
                return state
            else:
                return mzero
        lessThans = state.constraints.get("lt", frozenset())
        if varq(lessValue):
            (mostLiteral, leastSet) = ltWalk(lessValue, lessThans)
            if not varq(moreValue) and mostLiteral is not None:
                if mostLiteral < moreValue:
                    return make_constraint(state, False, lt, less, more)
                else:
                    return mzero
            else:
                if moreValue in leastSet:
                    return mzero
        if varq(moreValue):
            (leastLiteral, mostSet) = mtWalk(moreValue, lessThans)
            if not varq(lessValue) and leastLiteral is not None:
                if lessValue < leastLiteral:
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


def appendo(first, second, combined):
    return disj_x(conj_x(emptyo(first), eq(second, combined)),
                  conj_x(emptyo(second), eq(first,combined)),
                  call_fresh_x(lambda firstHead, firstTail, combinedTail:
                      conj_x(conso(firstHead, firstTail, first),
                             conso(firstHead, combinedTail, combined),
                             appendo(firstTail, second, combinedTail))))
