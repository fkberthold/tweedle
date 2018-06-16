from microkanren.urconstraintkanren import *

def deep_walk(term, substitution):
    value = walk(term, substitution)
    if isinstance(value, Link):
        if value.is_empty():
            return value
        else:
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
        newState = State(state.constraints, state.constraintFunctions, new_c, state.id, state.traceFun)
        state.trace(True, "CALL_FRESH_X(%s)<IN>" % str(new_vars))
        succeeds = False
        for state_ in fun(newState):
            succeeds = True
            yield state_
        state.trace(succeeds, "CALL_FRESH_X(%s)<OUT>" % str(new_vars))
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
        newState = State(state.constraints, state.constraintFunctions, new_c, state.id, state.traceFun)
        state_generator = fun(newState)
        state.trace(True, "CALL_FRESH_X(%s)<IN>" % str(new_vars))
        succeeds = False
        for gen_state in state_generator:
            succeeds = True
            constraints = gen_state.constraints
            constraintFunctions = gen_state.constraintFunctions
            count = gen_state.count
            old_eq = constraints.get('eq', frozenset())
            output = [deep_walk(var, old_eq) for var in new_vars]
            yield output
        state.trace(succeeds, "CALL_FRESH_X(%s)<OUT>" % str(new_vars))
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
        return trace_with(eq(lst, Link(head, tail)), "conso")
    elif isinstance(lst, Link) and not lst.is_empty():
        return trace_with(conj(eq(head, lst.head),
                               eq(tail, lst.tail)), "conso")
    else:
        return trace_with(lambda state: mzero, "conso")

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
                state.trace(True, "lt(%s, %s)" % (lessValue, moreValue))
                return state
            else:
                state.trace(False, "lt(%s, %s)" % (lessValue, moreValue))
                return mzero
        lessThans = state.constraints.get("lt", frozenset())
        if varq(lessValue):
            (mostLiteral, leastSet) = ltWalk(lessValue, lessThans)
            if not varq(moreValue) and mostLiteral is not None:
                if mostLiteral + 1 == moreValue:
                    return make_constraint(state, False, eq, less, mostLiteral)
                else:
                    return make_constraint(state, mostLiteral >= moreValue, lt, less, more)
            else:
                if moreValue in leastSet:
                    state.trace(False, "lt(%s, %s)" % (lessValue, moreValue))
                    return mzero
        if varq(moreValue):
            (leastLiteral, mostSet) = mtWalk(moreValue, lessThans)
            if not varq(lessValue) and leastLiteral is not None:
                if leastLiteral - 1 == lessValue:
                    return make_constraint(state, False, eq, more, leastLiteral)
                else:
                    return make_constraint(state, lessValue >= leastLiteral, lt, less, more)
            else:
                if lessValue in mostSet:
                    state.trace(False, "lt(%s, %s)" % (lessValue, moreValue))
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
                state.trace(True, "incro(%s, %s)" % (augend, total))
                yield state
            else:
                state.trace(False, "incro(%s, %s)" % (augend, total))
                yield from mzero
    return generate(incroHelp)

def decro(minuend, difference):
    return incro(difference, minuend)

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
                state.trace(True, "addo(%s, %s, %s)" % (augend, addend, total))
                yield state
            else:
                state.trace(False, "addo(%s, %s, %s)" % (augend, addend, total))
                yield from mzero
        elif varCount == 1:
            if varq(augend_):
                yield from eq(augend_, total_ - addend_)(state)
            elif varq(addend_):
                yield from eq(addend_, total_ - augend_)(state)
            else:
                yield from eq(total_, augend_ + addend_)(state)
        else:
            yield from make_constraint(state, False, addo, augend_, addend_, total_)
    return generate(addoHelp)

def leno(lst, length):
    def lenoHelp(state):
        substitution = state.constraints.get("eq", frozenset())
        lst_ = walk(lst, substitution)
        length_ = walk(length, substitution)

        if varq(lst_) and varq(length_):
            yield from make_constraint(state, False, leno, lst_, length_)
        elif varq(lst_):
            new_list = Link()
            var_number = state.count - 1
            for var_number in range(state.count, state.count + length_):
                new_list = Link(var(var_number), new_list)
            newState = State(state.constraints, state.constraintFunctions, var_number + 1, state.id, state.traceFun)
            yield from eq(lst_, new_list)(newState)
        else:
            temp_lst = lst_
            size = 0
            while temp_lst != () and not varq(temp_lst) and not temp_lst.is_empty():
                temp_lst = temp_lst.tail
                size += 1
            if varq(temp_lst):
                yield from call_fresh(lambda len_rest: conj_x(addo(size, len_rest, length_),
                                                              leno(temp_lst, len_rest)))(state)
            else:
                yield from eq(length_, size)(state)
    return generate(lenoHelp)

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
    def indexo_help(state):
        substitution = state.constraints.get("eq", frozenset())
        lst_ = walk(lst, substitution)
        elem_ = walk(elem, substitution)
        index_ = walk(index, substitution)

        if varq(lst_):
            yield from make_constraint(state, False, indexo, lst_, elem_, index_)
        elif not isinstance(lst_, Link):
            yield from make_constraint(state, True, indexo, lst_, elem_, index_)
        else:
            temp_lst = lst_
            curr_index = 0
            while temp_lst != () and not varq(temp_lst) and not temp_lst.is_empty():
                if not varq(index_):
                    if curr_index == index_:
                        yield from eq(elem_, temp_lst.head)(state)
                        return
                    elif curr_index > index_:
                        return
                else:
                    yield from conj(eq(index_, curr_index),
                                    eq(elem_, temp_lst.head))(state)
                curr_index += 1
                temp_lst = temp_lst.tail

            if varq(temp_lst):
                if varq(index_):
                    yield from call_fresh(lambda new_index:
                                          conj_x(indexo(temp_lst, elem_, new_index),
                                                 addo(curr_index, new_index, index)))(state)

                elif curr_index <= index_:
                    yield from make_constraint(state, False, indexo, temp_lst, elem_, index_ - curr_index)
    return generate(indexo_help)

def when_known(value, goal):
    def when_known_help(state):
        substitution = state.constraints.get("eq", frozenset())
        value_ = walk(value, substitution)
        if varq(value_):
            yield from make_constraint(state, False, when_known, value_, goal)
        else:
            yield from goal(state)
    return generate(when_known_help)

def inserto(without_index, index, with_index):
    """Remove the indexth value of the given linked list. If the index
    is out past the end of the list, fails."""
    return call_fresh_x(lambda with_head, with_tail, without_head, without_tail, decr_index:
                        disj_x(conj_x(eq(index, 0),
                                      conso(with_head, without_index, with_index)),
                               conj_x(gt(index, 0),
                                      conso(with_head, with_tail, with_index),
                                      conso(without_head, without_tail, without_index),
                                      eq(with_head, without_head),
                                      decro(index, decr_index),
                                      inserto(without_tail, decr_index, with_tail))))

def for_last(value, goal):
    def for_last_help(state):
        substitution = state.constraints.get("eq", frozenset())
        value_ = walk(value, substitution)
        if(varq(value_)):
            return make_constraint(state, False, for_last, value_, goal)
        elif(isinstance(value_, Link) or value_ == ()):
            if value == () or value_.is_empty():
                state.trace(False, "empty for_last %s can't apply" % goal)
                return mzero
            else:
                tail = walk(value_.tail, substitution)
                if(varq(tail)):
                    return make_constraint(state, False, for_last, value_, goal)
                elif(isinstance(tail, Link) or tail == ()):
                    if tail == () or tail.is_empty():
                        return goal(value_.head)(state)
                    else:
                        return for_last(tail, goal)(state)
                else:
                    state.trace(False, "%s for_last %s is not a Link" % (tail, goal))
                    return mzero
        else:
            state.trace(False, "%s for_last %s is not a Link" % (value_, goal))
            return mzero
    return generate(for_last_help)


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
    return between_all(tower, lt)

def is_hanoi(hanoi):
    """A set of hanoi towers must have at least 3 towers total. Anything less
    will only work for special cases, so we disallow them."""
    is_3 = call_fresh_x(lambda tower1, tower2, tower3:
                        eq(hanoi, list_to_links([tower1, tower2, tower3])))
    return conj_x(is_3,
                  for_all(hanoi, is_tower))

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
                                 indexo(newState, toTower, toIndex),
                                 not_emptyo(toTower))))))

def hanoi_size(hanoi, size):
    return disj_x(conj_x(emptyo(hanoi),
                         eq(size, 0)),
                  call_fresh_x(lambda head, tail, head_size, tail_size:
                        conj_x(conso(head, tail, hanoi),
                               leno(head, head_size),
                               hanoi_size(tail, tail_size),
                               addo(head_size, tail_size, size))))

def equal_except_from_to(list1, list2, toIndex, fromIndex):
    """This is is a helper function for step_pair"""
    return call_fresh_x(lambda l1without_to, l2without_to, both_without:
                        conj_x(inserto(l1without_to, toIndex, list1),
                               inserto(l2without_to, toIndex, list2),
                               inserto(both_without, fromIndex, l1without_to),
                               inserto(both_without, fromIndex, l2without_to)))

def step_pair(stepBefore, stepAfter):
    return conj_x(is_step(stepBefore),
                  is_step(stepAfter),
                  call_fresh_x(lambda actionBefore, actionFromIndex, actionToIndex, stateBefore, stateAfter, discs, towers:
                               conj_x(eq(stepBefore, Link(actionBefore, stateBefore)),
                                      eq(stepAfter, Link(Link(actionFromIndex, actionToIndex), stateAfter)),
                                      call_fresh_x(lambda beforeFromStack, beforeToStack, afterFromStack, afterToStack, movingDisc:
                                            conj_x(equal_except_from_to(stateBefore, stateAfter, actionToIndex, actionFromIndex),
                                                   indexo(stateBefore, beforeFromStack, actionFromIndex),
                                                   indexo(stateBefore, beforeToStack, actionToIndex),
                                                   indexo(stateAfter, afterFromStack, actionFromIndex),
                                                   indexo(stateAfter, afterToStack, actionToIndex),
                                                   conso(movingDisc, afterFromStack, beforeFromStack),
                                                   conso(movingDisc, beforeToStack, afterToStack))),
                                      leno(stateBefore, 3),
                                      leno(stateAfter, 3),
                                      hanoi_size(stateAfter, 3),
                                      hanoi_size(stateBefore, 3))))

def hanoi_path(path):
    return between_all(path, step_pair)

def solve_hanoi(start_state, path, end_state):
    def walk_path(sub_path):
        return call_fresh_x(lambda last_action:
                            disj_x(eq(sub_path, Link(Link(last_action, end_state))),
                                   call_fresh_x(lambda next_action_state, next_path:
                                                conj_x(conso(next_action_state, next_path, sub_path),
                                                       absento(next_action_state, next_path),
                                                       walk_path(next_path)))))

    return call_fresh_x(lambda rest_path, last_action:
                        conj_x(conso(Link(Link(), start_state), rest_path, path),
                               walk_path(rest_path),
                               hanoi_path(path)))

