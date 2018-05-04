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
    def __init__(self, head=None, tail=()):
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
        if isinstance(tail, Link) and tail.is_empty():
            self._link = (head, ())
        else:
            self._link = (head, tail)

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
        if other == () and self.is_empty():
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
        if point_to.tail is ():
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

    @property
    def head(self):
        return self._link[0]

    @property
    def tail(self):
        return self._link[1]

    def is_empty(self):
        """Check if the list is `empty` which means both the `head` and `tail`
        are `None`.

        @return: True if empty, False otherwise.
        """
        return self.head is None and self.tail is ()

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
        for constraint in constraints:
            self.constraints[constraint] = frozenset(constraints[constraint])

    def __eq__(self, other):
        """When comparing two states for equality, we only compare the count and
        constraints value because comparing functions in python is a pointer
        comparison.

        @param other: The state being compared to.
        @return: True if both the counts and constraints are the same.
        """
        assert isinstance(other, State)
        if self.count == other.count and self.constraints == other.constraints:
            return True
        else:
            return False

    def __repr__(self):
        """This tries to display the state in a reasonably readable format
        as:
          Count: 2
          Constraints:
              Eq:
                  (var(0), 3)
                  (var(1), var(0))

        @return: A string representing the state.
        """
        constraint_str = ""
        for constraint in self.constraints:
            constraint_str += "\t%s:\n" % constraint
            for constraint_arguments in self.constraints[constraint]:
                constraint_str += "\t\t%s\n" % repr(constraint_arguments)
        return "\nCount: %i\nConstraints:\n%s" % (self.count, constraint_str)

def var(identifier, name=None):
    """A wrapper that creates a LogicVariable. This is mostly to match other
    implementations and save a few keystrokes.

    This will rarely be used in normal code. The most common usage will be
    in the creation of new constraints and testing. Otherwise you'll bring
    variables in via the `call_fresh` function.

    @param identifier: A numeric identifier for a new LogicVariable.
    @param name: An optional name for the new LogicVariable.
    @return: A new LogicVariable.
    """
    return LogicVariable(identifier, name)


def varq(value):
    """Determine if a value is a LogicVariable.

    @param value: This can be any value, but will generally be a term in the
    logic system.
    @return: True if the value is a LogicVariable, False otherwise.
    """
    return isinstance(value, LogicVariable)

def vareq(x1, x2):
    """Determine if two vars are equal. This does not check if they're values
    are the same, but if they are exactly the same pointer.

    Also note that it makes no difference at all if they have the same `name`
    value.

    @param x1: A Logic Variable
    @param x2: Another Logic Variable
    @return: True if they have the same id.
    """
    return x1.id  == x2.id

def walk(term, substitution):
    """Walk is a helper function for dealing with the equality constraint.
    it repeatedly walks through the substitution replacing term's LogicVariable
    values until term doesn't contain any LogicVariables that are on the left
    side in the substitution.

    @param term: The original term to search for.
    @return: A literal value or LogicVariable depending on what the substitution
    contains.
    """
    if varq(term):
        values = [value for (t, value) in substitution if t == term]
        assert len(values) <= 1
        if values == []:
            return term
        elif varq(values[0]):
            return walk(values[0], substitution)
        else:
            return values[0]
    else:
        return term

def ext_s(variable, value, substitution):
    """ext_s is a helper function for eq, without checking for duplicates or
    contradiction it adds a variable/value pair to the given substitution.
    `unify` deals with all of the related verification.

    @param variable: A LogicVariable
    @param value: A value that can either be a LogicVariable or literal.
    @param substitution: A set of tuples indicating equality for LogicVariables.
    @return: A new substitution with variable and value set as being equal.
    """
    return substitution | {(variable, value)}

# The state when there is a contradiction in terms.
mzero = iter([])

def unit(state):
    """Used for lifting a new stream of states into a goal.

    @param state: A State object to be streamed.
    @return: A generator yielding a single State.
    """
    yield state

def unify(left, right, substitution):
    """unify is a helper function and the core for eq. unify will
    recursively look up both `left` and `right` in substitution using the `walk`
    function.

    After getting each of their associated values, they are compared.
       If they are equal either as variables or literals, no change is made and
          the original substitution is returned.
       If either of the values is a LogicVariable, then the pair of values is
          added to the `substitution` via ext_s.
       If both of the values is a Link (linked list), then each of their values
          is unified in turn, if any of their values fails unificaiton, then
          `left` and `right` also fail.
       If the the values are literals or both variables and not equal, then
          unification fails and the state will be found to be invalid.

    @param left: The left term in an equality goal.
    @param right: The right term in an equality goal.
    @param substitution: A set of paired terms in the form {(left, right)} which
    assert that left == right.
    @return: A valid substitution if `left` and `right` unify, False otherwise.
    """
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

def generate(goal):
    """generate is used to simplify writing goals.  It's intended that when we
    author new goals we can do so without worrying whether those goals will be
    passed a single state, or stream of states.

    generate will either read a state or stream of states and feed one state
    at a time to `goal`, it will then yield a stream of states.

    @param goal: A goal that may or may not yield a stream of states.
    @return: A stream of states.
    """
    def generate_help(state):
        if isinstance(state, types.GeneratorType):
            for genState in state:
                result = goal(genState)
                if isinstance(result, State):
                    yield result
                else:
                    yield from result
        else:
            result = goal(state)
            yield from applyConstraints(result)
    return generate_help

def eq(left, right):
    """eq is the first and most common constraint.  It constrains `left` and
    `right` to be the same value.

    @param left: Either a LogicVariable or literal.
    @param right: Either a LogicVariable or literal.
    @return: A function that takes a state and returns a stream of states.
    """
    def eqHelp(state):
        substitution = state.constraints.get("eq", frozenset())
        unified = unify(left, right, substitution)
        if isinstance(unified, frozenset):
            constraints = {**state.constraints, **{"eq":unified}}
            constraint_funcs = {**state.constraintFunctions, **{"eq":eq}}
            return State(constraints, constraint_funcs, state.count)
        else:
            return mzero
    return generate(eqHelp)

def make_constraint(state, fails, function, *args):
    """A small helper function for constructing new constraints, it takes care
    most of the standard chores of adding the new function and terms to the
    State.

    @param state: The state that's changing.
    @param fails: If false, then the state is invalid an mzero is returned, this
    is used to simplify the constraint itself.
    @param function: The constraint function to be added to the state.
    @param *args: Each of the arguments to be added.
    @return: A stream containing either no state or a single state.
    """
    if fails:
        return mzero
    else:
        name = function.__name__
        constraint = state.constraints.get(name, frozenset())
        constraints = {**state.constraints, **{name:constraint | {args}}}
        constraint_funcs = {**state.constraintFunctions, name:function}
        return unit(State(constraints, constraint_funcs, state.count))

def neq(left, right):
    """Asserts that the `left` value is not equal to the `right` value.

    @param left: A literal or LogicVariable
    @param right: A literal or LogicVariable
    @return: A function that takes a state and returns a stream of states.
    """
    def neqHelp(state):
        substitution = state.constraints.get("eq", frozenset())
        leftValue = walk(left, substitution)
        rightValue = walk(right, substitution)
        fails = any([leftValue == rightValue])
        return make_constraint(state, fails, neq, left, right)
    return generate(neqHelp)

def absento(elem, lst):
    """Asserts that `elem` is neither equal to `lst`, nor is it an element of
    `lst`.

    @param elem: A literal or LogicVariable that shouldn't be in `lst`.
    @param lst: A value that could either be a list or individual element.
    @return: A function that takes a state and returns a stream of states.
    """
    def absentoHelp(state):
        substitution = state.constraints.get("eq", frozenset())
        elemValue = walk(elem, substitution)
        lstValue = walk(lst, substitution)
        fails = any([elemValue == lstValue,
                     not varq(lstValue) and elemValue in lstValue])
        return make_constraint(state, fails, absento, elem, lst)
    return generate(absentoHelp)

def call_fresh(function):
    """call_fresh is used to instantiate new variables in the logic system.

    @param function: A single arity function that returns a goal.
    @return: The goal returned by function.
    """

    def call_fresh_help(state):
        count = state.count
        # Gets the names of the argument for 'function'
        name = list(signature(function).parameters)[0]
        new_var = var(count, name)
        goal = function(new_var)
        newState = State(state.constraints, state.constraintFunctions, count+1)
        yield from goal(newState)
    return generate(call_fresh_help)

def disj(g1, g2):
    """Take two relations, pass the state to each of them separately, yield a
    stream of states alternately from each relation.  This is equivalent to an
    xor boolean operation.

    @param g1: A relation.
    @param g2: A relation.
    @return: A function that reads a stream of states and outputs the states
    yielded from each realation.
    """

    def disj_help(state):
        yield from mplus(g1(state), g2(state))
    return generate(disj_help)

def conj(g1, g2):
    """Take two relations, pass the state to the first relation, then pass each
    state that it yields to the second relation, then yields the result.  This
    is equivalent to an and boolean operation.

    @param g1: A relation.
    @param g2: A relation.
    @return: A function that streams a state through both g1 and g2.
    """
    def conj_help(state):
        yield from bind(g1, g2)(state)
    return generate(conj_help)

def applyConstraints(state):
    """For the given state, consecutively applies all of it's exiting
    constraints to determine if a change in the state breaks one of the existing
    constraints.

    @param state: The state getting verified.
    @return: A stream of states resulting from the application of the
    constraints.
    """
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
    """mplus is a monad thing, don't worry about the name.

    The easy explanation is, given two streams of states it will alternately
    take a value from each one, so assuming each state has a stream like:

    state_stream1 = [state1a, state1b, state1c]
    state_stream2 = [state2a, state2b, state2c]

    This will yield:

    [state1a, state2a, state1b, state2b, state1c, state2c]

    If either of the streams run out, then the remainder of the states from the
    other stream are yielded.

    @param state_stream1: A stream of zero or more states.
    @param state_stream2: A stream of zero or more states.
    @return: The combined states from state_stream1 and state_stream2
    """
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
    """Bind combines two goals by threading the results of goal1 through goal2.

    @param goal1: Any goal.
    @param goal2: Any goal.
    @return: A new goal that given a state will yield the results of applying
    goal1 to that state, then threading the results through goal2.
    """
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
