import types
from inspect import signature

"""UrKanren

The following is intended to help both myself and others understand micro-kanren constraints.

While the overall goal of this project is to make a fully Pythonic Kanren, for the
purposes of this file the emphasis is clarity, particularly for those who are using
it to supliment reading papers on the subject.

The papers I've found to be the most illuminating and which have directly impacted
the design here are:

µKanren: A Minimal Functional Core for Relational Programming
    http://webyrd.net/scheme-2013/papers/HemannMuKanren2013.pdf
"""

class Link(object):
    """A Lisp style linked list.

    "What?" I hear you ask, "This is Python we have plenty of very nice
    data structures, why on Earth would we want Lisp style lists?"

    And that's true, for getting real work done, I'll take Python lists over
    linked lists any day.

    But. One of the interesting things you can do in micro-kanren is represent
    cases where you know things about the front of a list and have no idea how
    long the list is.  For example, I could say that I know for the list `l` that
    `l[0] == 'cake'`, and that is all I know about the list. It may have 100 values,
    or `'cake'` may be all there is. This is very hard to represent using Python lists,
    but in this style of linked list can be represented like this: `Link('cake', LogicVariable(0))`
    """
    def __init__(self, head=None, tail=None):
        self.head = head
        if isinstance(tail, type(self)) and tail.is_empty():
            self.tail = None
        else:
            self.tail = tail

    def __repr__(self):
        if self.is_empty():
            return "()"
        point_to = self
        str_repr = "(%s" % str(self.head)
        while isinstance(point_to.tail, type(self)):
            point_to = point_to.tail
            str_repr += " "
            str_repr += "%s" % str(point_to.head)
        if point_to.tail is None:
            str_repr += ")"
        else:
            str_repr += " . %s)" % str(point_to.tail)
        return str_repr

    def is_empty(self):
        return self.head is None and self.tail is None

def listToLinks(lst):
    """Linked Lists are a neat, elegant data structure...
    And a pain to code by hand.
    @param lst: The python list structure to convert.
    @return: A linked list converted from the `lst`.`
    """
    assert isinstance(lst, list), "Only lists can be convernted to Links."
    if lst == []:
        return Link()
    else:
        if isinstance(lst[0], list):
            return Link(listToLinks(lst[0]), listToLinks(lst[1:]))
        else:
            return Link(lst[0], listToLinks(lst[1:]))

class LogicVariable(object):
    """This is a minor deviation from how most of the papers handle logic variables.
    The various scheme dialects aren't big on classes, so they chose instead to just
    represent logic variables as integers.
    This is terrible for clarity, and makes it hard to attach other data to your
    variable, like a name.
    """
    def __init__(self, identifier, name=None):
        self.id = identifier
        self.name = name

    def __eq__(self, other):
        return isinstance(other, LogicVariable) and self.id == other.id

    def __repr__(self):
        """Why are LogicVariables preceded by `+`? First because I wanted to make it
        clear when something was a LogicVariable and not just an integer. Second the
        `+` unary operator in Python is how we're creating LogicVariables in the main
        code base."""
        if self.name:
            return "+%s(%i)" % (self.name, self.id)
        else:
            return "+%i" % self.id

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
    elif isinstance(left, Link) and isinstance(right, Link):
        headSub = unify(left.head, right.head, substitution)
        if headSub is not False:
            return unify(left.tail, right.tail, headSub)
        else:
            return False
    elif left == right:
        return substitution
    else:
        return False

def call_fresh(function):
    """Takes a *-arity function which returns a list of states.  It assigns the given argument
        an unassigned term.  It then returns a function that takes a state and returns a list of
        states."""
    def call_fresh_help(state):
        count = state.count
        name = list(signature(function).parameters)[0]  # Gets the names of all of the arguments for 'function'
        new_var = var(count, name)
        goal = function(new_var)
        newState = State(state.substitution, count + 1)
        yield from goal(newState)
    return generate(call_fresh_help)

def disj(g1, g2):
    """Take multiple relations. For each one that evaluates true, concatenate and return
        it's results."""
    def disj_help(state):
        yield from mplus(g1(state), g2(state))
    return generate(disj_help)

def conj(g1, g2):
    """Take two relations. Determine the result if both are true."""
    def conj_help(state):
        yield from bind(g1, g2)(state)
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

def mplus(state_stream1, state_stream2):
    stateStreams = [state_stream1, state_stream2]
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

def bind(goal1, goal2):
    def bind_help(state):
        goals = [goal1, goal2]
        stateStreams = []
        newStreams = []
        for state in goal1(state):
            stateStreams = [goal2(unit(state))]
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
