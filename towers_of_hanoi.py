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
            old_eq = constraints.get('eq', frozenset())
            output = [deep_walk(var, old_eq) for var in new_vars]
            yield output
    return call_fresh_help

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
    elif isinstance(lst, Link) and not lst.is_empty():
        return conj_x(eq(head, lst.head),
                     eq(tail, lst.tail))
    else:
        return lambda state: mzero

def lt(less, more):
    def ltWalk(term, lessThans):
        """Given a term and a set of lessThan constraints, returns the highest known
        literal that is still less than the term and a list of variable terms that are
        also less than term."""
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
        """Given a term and a set of lessThan constraints, returns the lowest known
        literal that is still more than the term and a list of variable terms that are
        also more than term."""
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
                if mostLiteral + 1 == moreValue:
                    return make_constraint(state, False, eq, less, mostLiteral)
                elif mostLiteral < moreValue:
                    return make_constraint(state, False, lt, less, more)
                else:
                    return mzero
            else:
                if moreValue in leastSet:
                    return mzero
        if varq(moreValue):
            (leastLiteral, mostSet) = mtWalk(moreValue, lessThans)
            if not varq(lessValue) and leastLiteral is not None:
                if leastLiteral - 1 == lessValue:
                    return make_constraint(state, False, eq, more, leastLiteral)
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

def incro(augend, total):
    """Assert that when augend is increased by one, the result is total."""
    def incroHelp(state):
        substitution = state.constraints.get("eq", frozenset())
        augend_ = walk(augend, substitution)
        total_ = walk(total, substitution)

        if varq(augend_) and varq(total_):
            yield from lt(augend, total)(make_constraint(state, False, incro, augend, total))
        elif varq(total_):
            yield from eq(total_, augend_ + 1)(state)
        elif varq(augend_):
            yield from eq(augend_, total_ - 1)(state)
        else:
            if augend_ + 1 == total_:
                yield state
            else:
                yield from mzero
    return generate(incroHelp)


def addo(augend, addend, total):
    """Addition will make the basis for doing arithmatic
    in constraint kanren."""
    def addoHelp(state):
        substitution = state.constraints.get("eq", frozenset())
        augend_ = walk(augend, substitution)
        addend_ = walk(addend, substitution)
        total_ = walk(total, substitution)

        varCount = len([val for val in [augend_, addend_, total_] if varq(val)])

        if varCount == 0:
            if augend_ + addend_ == total_:
                yield state
            else:
                yield from mzero
        elif varCount == 1:
            if varq(augend_):
                yield from eq(augend_, total_ - addend_)(state)
            elif varq(addend_):
                yield from eq(addend_, total_ - augend_)(state)
            else:
                yield from eq(total_, augend_ + addend_)(state)
        else:
            yield from make_constraint(state, False, addo, augend, addend, total)
    return generate(addoHelp)

def leno(lst, length):
    empty_list_0 = conj_x(emptyo(lst),
                          eq(length, 0))
    not_empty = call_fresh_x(
        lambda head, tail, decrement:
        conj_x(not_emptyo(lst),
               lt(0, length),
               conso(head, tail, lst),
               leno(tail, decrement),
               incro(decrement, length)))
    return disj(empty_list_0, not_empty)

def appendo(first, second, combined):
    first_empty = conj_x(emptyo(first),
                         eq(second, combined))
    second_empty = conj_x(not_emptyo(first),
                          emptyo(second),
                          eq(first,combined))
    neither_empty = call_fresh_x(
        lambda firstHead, firstTail, combinedTail:
        conj_x(not_emptyo(first),
               not_emptyo(second),
               conso(firstHead, firstTail, first),
               conso(firstHead, combinedTail, combined),
               appendo(firstTail, second, combinedTail)))
    return disj_x(first_empty, second_empty, neither_empty)

def indexo(lst, elem, index):
    def elem_is_head(head):
        return conj_x(eq(index, 0),
                      eq(head, elem))
    def elem_is_in_tail(tail):
        return call_fresh_x(lambda decrement:
                            conj_x(incro(decrement, index),
                                   indexo(tail, elem, decrement)))
    return call_fresh_x(lambda head, tail:
                        conj_x(not_emptyo(lst),
                               lt(-1, index),
                               conso(head, tail, lst),
                               disj_x(elem_is_head(head),
                                      elem_is_in_tail(tail))))

def is_action(action):
    """An action is in the form (newLocation . oldLocation) where the locations
    are indexes of towers, starting at 0. eg. (0 . 2) moves a disk from tower 0
    to tower 2.
    """
    return disj_x(eq(action, Link()),
                 call_fresh_x(lambda oldLocation, newLocation:
                              conj(eq(action, Link(oldLocation, newLocation)),
                                      not_emptyo(action))))

def is_tower(tower):
    empty_tower = emptyo(tower)
    one_disc_tower = leno(tower, 1)
    multi_disc_tower = call_fresh_x(
        lambda upperDisc, lowerDisc, withoutUpper, withoutLower:
        conj_x(conso(upperDisc, withoutUpper, tower),
               not_emptyo(withoutUpper),
               conso(lowerDisc, withoutLower, withoutUpper),
               lt(upperDisc, lowerDisc),
               is_tower(withoutUpper)))
    return disj_x(empty_tower, one_disc_tower, multi_disc_tower)

def is_hanoi(hanoi):
    """A set of hanoi towers must have at least 3 towers total. Anything less
    will only work for special cases, so we disallow them."""
    def all_towers(towers):
        no_towers = emptyo(towers)
        some_towers = call_fresh_x(
            lambda head, tail:
            conj_x(not_emptyo(towers),
                   conso(head, tail, towers),
                   is_tower(head),
                   all_towers(tail)))
        return disj(no_towers, some_towers)
    more_than_2 = call_fresh_x(lambda length:
                               conj(leno(hanoi, length),
                                    lt(2, length)))
    return conj_x(all_towers(hanoi),
                  more_than_2)

def is_step(step):
    """Steps are of the form: (action, hanoi_tower_set), where hanoi_tower_set
    is the current world state and action is the action that lead to that state.
    If the action is an empty link, then it's the start state."""
    return call_fresh_x(
        lambda action, newState:
        conj_x(conso(action, newState, step),
               is_action(action),
               is_hanoi(newState),
               disj_x(emptyo(action),
                      call_fresh_x(
                          lambda fromIndex, toIndex, toTower:
                          conj_x(conso(fromIndex, toIndex, action),
                                 indexo(toTower, toIndex, newState),
                                 not_emptyo(toTower))))))
