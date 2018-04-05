import types
from inspect import signature

"""UrConstraintKanren

The following is intended to help both myself and others understand micro-kanren with
constraints.

While the overall goal of this project is to make a fully Pythonic Kanren, for the
purposes of this file the emphasis is clarity, particularly for those who are using
it to supliment reading papers on the subject.

The papers I've found to be the most illuminating and which have directly impacted
the design here are:

A Framework for Extending microKanren with Constraints
    https://arxiv.org/pdf/1701.00633

In this file, the above paper will be referenced as FEMC.
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

    def __eq__(self, other):
        if other is None and self.is_empty():
            return True
        if not isinstance(other, Link):
            return False
        elif self.is_empty() and other.is_empty():
            return True
        elif self.head == other.head:
            return self.tail == other.tail
        else:
            return False

    def __repr__(self):
        if self.is_empty():
            return "()"
        point_to = self
        str_repr = "(%s" % repr(self.head)
        while isinstance(point_to.tail, type(self)):
            point_to = point_to.tail
            str_repr += " "
            str_repr += "%s" % repr(point_to.head)
        if point_to.tail is None:
            str_repr += ")"
        else:
            str_repr += " . %s)" % repr(point_to.tail)
        return str_repr

    def __hash__(self):
        return self.head.__hash__() + self.tail.__hash__()

    def __contains__(self, elem):
        if self.head == elem:
            return True
        elif isinstance(self.tail, type(self)):
            return self.tail.__contains__(elem)
        else:
            return self.tail == elem

    def is_empty(self):
        return self.head is None and self.tail is None

def list_to_links(lst):
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
            return Link(list_to_links(lst[0]), list_to_links(lst[1:]))
        else:
            return Link(lst[0], list_to_links(lst[1:]))

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
            return "var(%i, '%s')" % (self.id, self.name)
        else:
            return "var(%i)" % self.id

    def __hash__(self):
        return self.id

class State(object):
    """That the list of constraints is not pre-baked into the state is a key
    deviation from FEMC.  I chose this route because it makes implementation
    easier to write and understand and because it makes the implementaiton itself
    more flexible."""
    def __init__(self, constraints={}, count=0):
        assert count >= 0
        self.count = count
        self.constraints = {}
        if constraints:
            for constraint in constraints:
                self.constraints[constraint] = frozenset(constraints[constraint])
    def __eq__(self, other):
        assert isinstance(other, State)
        return self.count == other.count and self.constraints == other.constraints

    def __repr__(self):
        constraint_str = ""
        for constraint in self.constraints:
            constraint_str += "\t%s:\n" % constraint
            for constraint_arguments in self.constraints[constraint]:
                constraint_str += "\t\t%s\n" % repr(constraint_arguments)
        return "\nCount: %i\nConstraints:\n%s" % (self.count, str(constraint_str))

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
        values = [value for (t, value) in substitution if t == term]
        assert len(values) <= 1, "Something has gone horribly wrong we've asserted %s could be the following, any given value can only equal one thing: %s" % (str(term), str(values))
        if values == []:
            return term
        elif isinstance(values[0], LogicVariable):
            return walk(values[0], substitution)
        else:
            return values[0]
    else:
        return term

def ext_s(variable, value, substitution):
    """Add a value v to variable x for the given substitution s"""
    return substitution | {(variable, value)}

# The state when there is a contradiction in terms.
mzero = iter([])

def unit(state):
    """Don't change anything"""
    yield state

def unify(left, right, substitution):
    """Given a pair of terms determines if they can be equivalent.
        If they are both the same established value, returns the substitution.
        If one or the other value is unknown, then updates the substitution with
            the unkown value being set to the known value.
        If they can't be unified then returns False."""
    leftValue = walk(left, substitution)
    rightValue = walk(right, substitution)
    if varq(leftValue) and varq(rightValue) and vareq(leftValue, rightValue):
        return substitution
    elif varq(leftValue):
        return ext_s(leftValue, right, substitution)
    elif varq(rightValue):
        return ext_s(rightValue, left, substitution)
    elif isinstance(leftValue, Link) and isinstance(rightValue, Link):
        headSub = unify(leftValue.head, rightValue.head, substitution)
        if headSub is not False:
            return unify(leftValue.tail, rightValue.tail, headSub)
        else:
            return False
    elif leftValue == rightValue:
        return substitution
    else:
        return False

def eq(left, right):
    """Returns a function that takes a state/count object and returns
        a list of new state/count objects.
       If left and right are both set terms, determines if they are the same.
           If they are, returns the state as is.
           If they are not, then returns an empty state.
       If left or right is a variable, then asserts they are equal and adds it to,
          the state. If they are not equal, then returns an empty state."""
    def eqHelp(state):
        substitution = state.constraints.get("eq", frozenset())
        unified = unify(left, right, substitution)
        if isinstance(unified, frozenset):
            return State({**state.constraints, **{"eq":unified}}, state.count)
        else:
            return mzero
    return generate(eqHelp)

def neq(left, right):
    """Asserts that the `left` value is not equal to the `right` value."""
    def neqHelp(state):
        substitution = state.constraints.get("eq", frozenset())
        leftValue = walk(left, substitution)
        rightValue = walk(right, substitution)
        fails = any([leftValue == rightValue])
        return make_constraint(state, fails, neq, left, right)
    return generate(neqHelp)

def absento(elem, lst):
    """Asserts that `elem` is neither equal to `lst`, nor is it an element of `lst`."""
    def absentoHelp(state):
        substitution = state.constraints.get("eq", frozenset())
        elemValue = walk(elem, substitution)
        lstValue = walk(lst, substitution)
        fails = any([elemValue == lstValue,
                     not varq(lstValue) and elemValue in lstValue])
        return make_constraint(state, fails, absento, elem, lst)
    return generate(absentoHelp)

def make_constraint(state, fails, function, *args):
    # Python reflection lets us pull the name of the function that was passed
    if fails:
        return mzero
    else:
        name = function.__name__
        constraint = state.constraints.get(name, frozenset())
        return unit(State({**state.constraints, **{name:constraint | {args}}}))

def call_fresh(function):
    """Takes a *-arity function which returns a list of states.  It assigns the given argument
        an unassigned term.  It then returns a function that takes a state and returns a list of
        states."""
    def call_fresh_help(state):
        count = state.count
        name = list(signature(function).parameters)[0]  # Gets the names of all of the arguments for 'function'
        new_var = var(count, name)
        goal = function(new_var)
        newState = State(state.constraints, count + 1)
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
    return generate(conj_help)

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
            yield from applyConstraints(result)
    return generate_help

def applyConstraints(state):
    goal = unit
    if isinstance(state, State):
        for constraint in state.constraints:
            newgoal = eval(constraint)
            for args in state.constraints[constraint]:
                goal = bind(goal, newgoal(*args))
        yield from goal(state)
    else:
        for stateFromGen in state:
            yield from applyConstraints(stateFromGen)


def mplus(state_stream1, state_stream2):
    stateStreams = [state_stream1, state_stream2]
    newStreams = []
    while stateStreams:
        for stateStream in stateStreams:
            try:
                result = stateStream.__next__()
                yield result
# There was a time when this just wouldn't work without the commented code
#  below, I'm leaving this here while I continue to explore, but as far as
#  I can tell, you never end up with a stream returning a stream.
#                if isinstance(result, State):
#                    yield result
#                else:
#                    newStreams.append(result)  # TODO: Can this happen?
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
            stateStreams += [goal2(unit(state))]
            for stateStream in stateStreams:
                try:
                    result = stateStream.__next__()
                    yield result
# I don't think this can happen.
#                    if isinstance(result, State):
#                        yield result
#                    else:
#                        newStreams.append(result) # TODO: Can this happen?
                    newStreams.append(stateStream)
                except StopIteration:
                        pass
            stateStreams = newStreams
            newStreams = []
        while stateStreams:
            for stateStream in stateStreams:
                try:
                    result = stateStream.__next__()
                    yield result
# I don't think this can happen.
#                    if isinstance(result, State):
#                        yield result
#                    else:
#                        newStreams.append(result) # TODO: Can this happen?
                    newStreams.append(stateStream)
                except StopIteration:
                        pass
            stateStreams = newStreams
            newStreams = []

    return bind_help
