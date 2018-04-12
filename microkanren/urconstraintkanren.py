import types
from inspect import signature

"""UrConstraintKanren

The following is intended to help both myself and others understand micro-kanren
with constraints.

While the overall goal of this project is to make a fully Pythonic Kanren, for
the purposes of this file the emphasis is clarity, particularly for those who
are using it to supliment reading papers on the subject.

The papers I've found to be the most illuminating and which have directly
impacted the design here are:

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
    long the list is.  For example, I could say that I know for the list `l`
    that `l[0] == 'cake'`, and that is all I know about the list. It may have
    100 values, or `'cake'` may be all there is. This is very hard to represent
    using Python lists, but in this style of linked list can be represented like
    this: `Link('cake', LogicVariable(0))`
    """
    def __init__(self, head=None, tail=None):
        """For practical purposes this is a traditional value and pointer style
        of linked list. The head is the value the tail is the pointer.  If the
        tail is set to None, then it's a single value list, if the head is set
        to None, then it's an empty list. This means that `None` isn't on the
        list of values we can use in this logic system.

        Because we're implementing in the style of Lisp lists, `tail` doesn't
        have to be a link, but can be another value, creating a `dotted pair`,
        similar to a tuple in Python.

        @param head: The value for the link.
        @param tail: The rest of the list, if any, or another value.
        """
        self.head = head
        if isinstance(tail, type(self)) and tail.is_empty():
            self.tail = None
        else:
            self.tail = tail

    def __eq__(self, other):
        """Equality here tests first for if both qualify as empty lists. As
        mentioned above python's None is being treated as equivalent to an empty
        list, the same way scheme does with null.

        By Python convention if the type of `other` is different from `self`,
        then it's just not equal, as opposed to being a type error like it is in
        other languages.

        @param other: The value being compared for equality.
        @return: True if both are equal, false otherwise.
        """
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
        """I want to make it crystal clear to anyone using this code when
        they've encountered this style of list over Python lists, so the
        representation is in the Lisp style.

        @return: A string in the form of `(<value1> <value2> <value3>)` or
        `(<value1> . <value2>)` for dotted pairs.
        """
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
        """In order to use a list as a dictionary key, it needs to have a hash
        value. Just adding the hashes of head and tail is easy to implement and
        understand.

        @return: A reasonably unique hash.
        """
        return self.head.__hash__() + self.tail.__hash__()

    def __contains__(self, elem):
        """Returns true if `elem` is part of the list that this link is the
        front of.

        It could be argued that, if `elem` is a Link then you would check if:
            * head == elem
            * tail == elem
            * elem in tail

        That read is valid, but feels counter intuitive if you primarly think of
        Link as a way ot represent lists.

        @param elem: A value that may or may not be equal to the head of this
        Link, the tail of this Link (if it's a dotted pair) or in the tail of
        this Link.
        @return: True if this Link contains `elem`, false otherwise.
        """
        if self.head == elem:
            return True
        elif isinstance(self.tail, type(self)):
            return self.tail.__contains__(elem)
        else:
            return self.tail == elem

    def is_empty(self):
        """Check if the list is `empty` which means both the `head` and `tail`
        are `None`.

        @return: True if empty, False otherwise.
        """
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
    """This is a minor deviation from how most of the papers handle
    logicvariables. The various scheme dialects aren't big on classes, so they
    chose instead to just represent logic variables as integers.

    This is terrible for clarity, and makes it hard to attach other data to your
    variable.

    By making this a class you'll be able to see the name that was attached to,
    I promise this will make exploration easier and more interesting.
    """
    def __init__(self, identifier, name=None):
        """Logic Variables should only be instantiated using `call_fresh` in
        general usage.  If you instantiate one by hand you're asking for
        identifier conflict problems in your code and only have yourself to
        blame.

        @param: The unique identifier for this variable, in principle it could
        be any type. In practice it will be a positive integer or zero.
        @param: The name can be any string, when set in call_fresh it will
        be the same as the name of the argument it's taken from.
        """
        self.id = identifier
        self.name = name

    def __eq__(self, other):
        """Since the value of a LogicVariable is based on the State that
        contains, it and is not inherint to the variable itself, equality
        here is only by identifier, not by the value (if any) that it
        points to.

        @param other: The variable being compared for equality.
        @return: True if the id's are the same, False if they aren't or `other`
        isn't a LogicVariable.
        """
        return isinstance(other, LogicVariable) and self.id == other.id

    def __repr__(self):
        """`var` is the function generally used to instantiate a LogicVariable
        in other implementations, so for clarity I've used it here to represent
        the variable itself.

        @return: A string representing the LogicVariable, with `name` if
        present.
        """
        if self.name:
            return "var(%i, '%s')" % (self.id, self.name)
        else:
            return "var(%i)" % self.id

    def __hash__(self):
        """Given that the `id` is supposed to be unique in any context this is
        used, it's the obvious choise for a hash.

        @return: The ID as a unique hash.
        """
        return self.id

class State(object):
    """This contains the total state of a logic system at any point in time.
    This will consist of:
        constraints: A dictionary of constraints by name, each of which will
           contain the values to be tested by the constraint.
        constraintFunctions: This is just a bit redundant, it contains a
           dictionary of constraint functions, also by name. It's matched with
           `constraints` as the function to be executed on each of the set
           of arguments.
        count: Tracks the number of new LogicVariables that have been
           instantiated in this logic system and is used when selecting
           an identifier for new LogicVariables when instantiated.

    One major deviation in this module from FEMC is I've chosen not to pre-bake
    any kind of constraint into the State, they are discovered at the time that
    goals are processed.  I chose this because it makes it relatively easy to
    understand how new constraints are added.
    """
    def __init__(self, constraints={}, constraintFunctions={}, count=0):
        """In most of your usage, you'll instantiate State as empty, but will
        have to worry about adding new constraints and functions if you write
        a custom constraint. Fortunately we have functions further down to make
        that easier.

        @param constraints: A dictionary containing constraint names, each of
        which points to a frozenset of arguments to be passed to the constraint
        to determine if the constraint is met.
            eg {"eq":frozenset({(var(0, 'rabbit'), 'white'),
                                (var(1, 'queen'), 'red')})
        @param constraintFunctions: This allows us to add new kinds of
        constraint to the logic system on the fly. It will be a dictionary with
        the name of the constraint as key and the function as value.
            eg {'eq': <function <lambda> at 0x7f2529f7c950>}
        @param count: The number of LogicVariables that have been instantiated
        in the State.
        """
        assert count >= 0
        self.count = count
        self.constraints = {}
        self.constraintFunctions = constraintFunctions
        if constraints:
            self.constraints = {constraint:frozenset(constraint)}
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
            return State({**state.constraints, **{"eq":unified}}, {**state.constraintFunctions, **{"eq":eq}}, state.count)
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
        return unit(State({**state.constraints, **{name:constraint | {args}}}, {**state.constraintFunctions, name:function}, state.count))

def call_fresh(function):
    """call_fresh is used to instantiate new variables in the logic system.
    @param function: A single arity function that returns a goal.
    @return: The goal returned by function.
    """
    def call_fresh_help(state):
        count = state.count
        name = list(signature(function).parameters)[0]  # Gets the names of the argument for 'function'
        new_var = var(count, name)
        goal = function(new_var)
        newState = State(state.constraints, state.constraintFunctions, count + 1)
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
            newgoal = state.constraintFunctions[constraint]
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
                    newStreams.append(stateStream)
                except StopIteration:
                        pass
            stateStreams = newStreams
            newStreams = []

    return bind_help
