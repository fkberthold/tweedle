from microkanren.urconstraintkanren import *

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
        newState = State(state.substitution, new_c)
        yield from fun(newState)
    return generate(call_fresh_help)

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