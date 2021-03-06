import abc
import types
import collections
import copy
import traceback
import sys
import itertools
from inspect import signature

class LVar(object):
    """The objects instantiated by this class represent Logic Variables. Each should
    be unique across any given assertion.
    """
    nextId = 0  # Ensures uniqueness

    def __init__(self, name=None):
        """Each instance must have a unique id. `name` can be any string, they are used
        to clarify intent only and can be duplicated harmlessly.

        @param name: The name attached to the variable, `None` if it has no name.
        """
        self.id = LVar.nextId
        LVar.nextId += 1
        self.name = name

    def __repr__(self):
        """Represent the LVar with its unique ID and name if it has one.
        """
        if self.name:
            return "%s(%i)" % (self.name, self.id)
        else:
            return "%i" % self.id

    def __hash__(self):
        """Since all LVars are unqiue by id, it's id should be sufficient as a hash.
        """
        return self.id

def varq(value):
    """Test if `value` is a Logic Variable.
    """
    return isinstance(value, LVar)

def lvars(count):
    """Create `count` Logic Variables.

    @param count: The number of Logic Variables to return.
    """
    return [LVar() for n in range(0, count)]

class State(object):
    """Expresses the value of any given logic variables in a goal.
    """
    def __init__(self, substitution={}, valid=True):
        """Instatiate a new state, which may or may not be valid. If a state
        is not valid, then it's substitution value is irrelevant.

        @param substitution: The values of each Logic Variable in the State.
        @param valid: Whether the state is free of contradictions.  Generally even
                      if the state is not valid, it may not show in the substitution.
        """
        self.substitution = substitution
        self.valid = valid

    def __hash__(self):
        """Unique hash for any given State is needed for some portions of unit testing.
        """
        return hash((self.valid, tuple(self.substitution.keys()), tuple(self.substitution.values())))

    def __eq__(self, other):
        """Test equality with another state, needed for unit testing.

        @param: Another state object.
        @return: True if valid and substitution match.
        """
        assert isinstance(other, State)
        return self.valid == other.valid and self.substitution == other.substitution

    def __len__(self):
        """The size of a state is just the size of it's substitution table.
        """
        return len(self.substitution)

    def __getitem__(self, key):
        """Rather than directly getting the value of the key, get the fully reified value.
        This has the (possibly strange?) effect of, if the key isn't present, then it just
        returns the key value."""
        return self.reify(key)

    def __missing__(self, key):
        """Get item from substitution."""
        return self.substitution[key]

    def __repr__(self):
        """States are represented as a list of their substitutions if valid.
        """
        if self.valid:
            subs = ""
            for key in self.substitution:
                subs = subs + ("  %s: %s\n" % (repr(key), repr(self.substitution[key])))
            return "Substitutions:\n%s" % (subs)
        else:
            return "State Invalid"

    def update(self, substitution=None, valid=None):
        if valid == False:
            return State({}, valid=False)
        else:
            substitution = copy.copy(self.substitution) if substitution is None else substitution
            valid = self.valid if valid is None else valid
            return State(substitution, valid)

    def ext_s(self, additionalSubstitutions):
        """Add a value v to variable x for the substitution"""
        return self.update(substitution={**additionalSubstitutions, **self.substitution})

    def reify(self, term):
        """For a given term, search the state for that term.
             If that term isn't found, then return the term.
             If the term is found, then applies reify to the value it finds.
        @param: A logical variable, a constant, or a collection of terms.
        """
        newTerm = term
        while varq(newTerm) and newTerm in self.substitution:
            newTerm = self.substitution[newTerm]
        if isinstance(newTerm, list):
            newTerm = [self.reify(val) for val in newTerm]
            return newTerm
        else:
            return newTerm

# The null state, when no states are valid for the given goal.
mzero = iter([])

# Wrapper that lets you return a single generator of a given state.
#  This is most useful when you're creating basic goals.
def unit(state):
    yield state

class Goal(abc.ABC):
    """A goal is an assertion or set of assertions to which can be tested
    for truth, and will return the conditions under which it is true.
    """

    def __init__(self):
        """The last state generated by a given goal is stored to make it
        easier to debug.
        """
        self.lastState = None

    def __and__(self, other):
        """Allows two goals to be combined using `&`.
        """
        return Conj(self, other)

    def __or__(self, other):
        """Allows two goals to be combined using `|`.
        """
        return Disj(self, other)

    @abc.abstractmethod
    def __run__(self, state):
        """A place holder to be used by goals to execute a given state.  This is called
        by `run` which gives the standard interface for call.
        """
        return

    def run(self, state=State(), results=None):
        """Execute the goal against the given `state` expecting up to a certain
        number of `results`.
        @param state: If no state is given, then it will start on a valid, empty state.
        @param results: The maximum number of results to wait for.
        """
        if results is None:
            runner = self.__run__(state)
            while True:
                try:
                    self.lastState = runner.__next__()
                    if self.lastState.valid:
                        yield self.lastState
                except StopIteration:
                    return
        else:
            runner = self.__run__(state)
            for index in range(0, results):
                try:
                    self.lastState = runner.__next__()
                    if self.lastState.valid:
                        yield self.lastState
                except StopIteration:
                    return


class Relation(Goal, abc.ABC):
    """An abstract class for goals that represent relations between values.
    """
    pass

class Connective(Goal, abc.ABC):
    """An abstract class for goals that combine more than one other goal.
    """
    _goals = []

    @property
    def goals(self):
        return self._goals

    @goals.setter
    def goals(self, goals):
        self._goals = goals

class Eq(Relation):
    """Eq is used for unification.
       If the values are scalars, it check if they are equal and returns the state unchanged if they are, otherwise returns an invald state.
       If either value is a Logic Variable, it reifies and unifies their values.
       If both values are collections, then it unifies each of the values in the collection.
    """
    def __init__(self, left, right):
        """`left` and `right` are the two values to be unified."""
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return "Eq(%s,%s)" % (repr(self.left), repr(self.right))

    def __run__(self, state):
        """As described above, this reifies, then unifies `left` and `right` in reference to `state`."""
        left = state.reify(self.left)
        right = state.reify(self.right)
        # Same variable means they're equal.
        if varq(left) and varq(right) and left.id == right.id:
            yield state.update()
        # If just one is a variable, then adds the other as its value.
        elif varq(left):
            yield state.ext_s({left: right})
        elif varq(right):
            yield state.ext_s({right: left})
        # Strictly strings are a collection of... other strings.
        #  Seriously, who thought this was a good idea? It's freaking turtles all the way down.
        #  So they get to be a special case before we start dealing with collections.
        elif isinstance(left, str):
            if left == right:
                yield state.update()
            else:
                yield state.update(valid=False)
        # If it's a collection, then it has a length, so all collections should be caught by this.
        elif hasattr(left, '__len__') and hasattr(right, '__len__') and len(left) > 0 and len(left) == len(right):
            try: # Dictionary Case
                # If it's not a dictionary then it doesn't have keys, so this should
                #  filter out non-dictionaries under the 'better to ask forgiveness' policy
                #  Python likes.
                leftKeys = left.keys()
                rightKeys  = right.keys()
                justInLeft = leftKeys - rightKeys
                justInRight = rightKeys - leftKeys
                leftVars = {v for v in justInLeft if varq(v)}
                rightVars = {v for v in justInRight if varq(v)}
                leftLiterals = justInLeft - leftVars
                rightLiterals = justInRight - rightVars

                if len(leftLiterals) > len(rightVars) or len(rightLiterals) > len(leftVars):
                    # If there are more literals in one side that don't match than there are
                    # variables on the other side, then the two sides can't match.
                    return

                # The easy and clear case, equal keys don't need to be compared, they're equal,
                #  we just have to worry about their values.
                inBoth = leftKeys & rightKeys
                if inBoth:
                    baseGoal = Conj(*[Eq(left[key], right[key]) for key in inBoth])
                else:
                    baseGoal = None

                if leftVars or rightVars:
                    for combinationSet in self.setCombinations(leftVars, rightVars, leftLiterals, rightLiterals):
                        # Unify both the keys and their values.
                        differenceGoal = Conj(*[Conj(Eq(leftKey, rightKey), Eq(left[leftKey], right[rightKey])) for (leftKey, rightKey) in combinationSet])
                        if inBoth:
                            yield from Conj(baseGoal, differenceGoal).run(state)
                        else:
                            yield from differenceGoal.run(state)
                else:
                    yield from baseGoal.run(state)
                return
            except AttributeError as err:
                pass

            try: # Ordered Iterator Case
                # Ordered Iterators, generally these will be lists/arrays, but there are other cases.
                assert hasattr(left, '__getitem__') and hasattr(right, '__getitem__')
                yield from Conj(*[Eq(leftVal, rightVal) for (leftVal, rightVal) in zip(left, right)]).run(state)
                return
            except Exception as err:
                pass

            try: # Unordered Iterator Case
                # Unordered Iterators, sets, operate similarly to dictionaries.
                justInLeft = left - right
                justInRight = right - left
                leftVars = {v for v in justInLeft if varq(v)}
                rightVars = {v for v in justInRight if varq(v)}
                leftLiterals = justInLeft - leftVars
                rightLiterals = justInRight - rightVars

                if len(leftLiterals) > len(rightVars) or len(rightLiterals) > len(leftVars):
                    # If there are more literals in one side that don't match than there are
                    # variables on the other side, then the two sides can't match.
                    return

                if leftVars or rightVars:
                    for combinationSet in self.setCombinations(leftVars, rightVars, leftLiterals, rightLiterals):
                        differenceGoal = Conj(*[Eq(leftKey, rightKey) for (leftKey, rightKey) in combinationSet])
                        yield from differenceGoal.run(state)
                else:
                    yield state.update()
                return
            except Exception as err:
                return

        elif left == right:
            # If all else failes, just check if they're equal.
            yield state.update()
        else:
            yield state.update(valid=False)

    def setCombinations(self, leftVars, rightVars, leftLits, rightLits):
        """For a given set of variables and literals which are being compared, creates
        all possible pairings of vars -> lits and vars -> vars (if there are more
        variables than literals).
        """
        rightVarsLst = list(rightVars)
        rightLitsLst = list(rightLits)
        leastLvarRlit = min(len(leftVars), len(rightLits))
        leastRvarLlit = min(len(rightVars), len(leftLits))
        combinations = []

        for rightVarsPerm in itertools.permutations(rightVars):
            for leftVarsPerm in itertools.permutations(leftVars):
                leftVarsToLits = list(zip(leftVarsPerm[0:leastLvarRlit], rightLitsLst[0:leastLvarRlit]))
                leftVarsToVars = list(zip(leftVarsPerm[leastLvarRlit:], rightVarsPerm[leastRvarLlit:]))
                for leftLitsPerm in itertools.permutations(leftLits):
                    rightVarsToLits = list(zip(rightVarsPerm[0:leastRvarLlit], leftLitsPerm[0:leastRvarLlit]))
                    combinations.append(leftVarsToLits + rightVarsToLits + leftVarsToVars)
        return combinations

class Fail(Goal):
    """Always sets the state to failing.
    """
    def __run__(self, state):
        yield state.update(valid=False)

class Succeed(Goal):
    """Leaves the state at valid, a no-op.
    """
    def __run__(self, state):
        yield state.update()

class Fresh(Goal):
    """Fresh is used to bring new variables into an assertion.
    """
    def __init__(self, function):
        """Fresh will generally bring in the variables using a lambda function, with the
        new variables as its arguments: Fresh(lambda x: Eq(x, 3))"""
        super().__init__()
        self.function = function
        self.function_vars = None
        self.goal = None

    def __repr__(self):
        goal = self.getFunctionGoal()
        return "Fresh %s: %s" % (str(self.function_vars), str(type(self.goal)))

    def getFunctionGoal(self):
        """The function which is passed to Fresh should return a Goal.  This will create a list of Logic Variables
        and pass them into the function. If the goal has already been instantiated, then just returns the goal.
        """
        if self.goal:
            return self.goal
        else:
            # Abusing reflection to get the parameter names for the Logic Variables.
            params = signature(self.function).parameters
            arg_count = len(params)
            self.function_vars = lvars(arg_count)
            for (var, name) in zip(self.function_vars, params):
                var.name = name
            self.goal = self.function(*self.function_vars)
            return self.goal

    def __run__(self, state):
        goal = self.getFunctionGoal()
        yield from goal.run(state)

class Call(Fresh):
    """Call works almost exactly the same as Fresh, the only difference is that the state it returns
    will only contain the reified parameters of the function passed to it rather than all of the values
    in the original state.
    """
    def __run__(self, state):
        goal = self.getFunctionGoal()
        for result in goal.run(state):
            reified_state = {}
            for var in self.function_vars:
                reified_state[var] = result.reify(var)
            yield state.update(reified_state)

class Disj(Connective):
    """Disj, logical or, will take a list of goals as parameters and will return the
    states generated by each of them in tern.
    """
    def __init__(self, *goals):
        super().__init__()
        self.goals = list(goals)

    def __repr__(self):
        if self.goals:
            return " | ".join([("(%s)" % str(goal)) if isinstance(goal, Connective) else str(goal) for goal in self.goals])
        else:
            return "EMPTY DISJ"

    def __run__(self, state):
        goals = self.goals
        # Each goal generates its own state stream based on the same start state.
        stateStreams = [goal.run(state) for goal in goals]
        newStreams = []
        while stateStreams:
            # Read in a state from each stream in turn
            # If a stream is empty, then drop it from the list.
            for stateStream in stateStreams:
                try:
                    result = stateStream.__next__()
                    newStreams.append(stateStream)
                    yield result
                except StopIteration:
                    pass
            stateStreams=newStreams
            newStreams=[]

class Conj(Connective):
    """Conj, logical and, takes a list of goals as parameters, and will stream the states it's handed in through all of them. If
    any of them fail, all of them fail, otherwise it returns the states generated by passing through all of them.
    """
    def __init__(self, *goals):
        super().__init__()
        self.goals = list(goals)

    def __repr__(self):
        if self.goals:
            return " & ".join([("(%s)" % str(goal)) if isinstance(goal, Connective) else str(goal) for goal in self.goals])
        else:
            return "EMPTY CONJ"

    def __run__(self, state):
        """When pulling states from the goals, it does it using the same pattern as described in:
               http://webyrd.net/scheme-2013/papers/HemannMuKanren2013.pdf
        this ensures that even if one of the goals generates an infinite number of states, all of
        them will eventually trickle through.
        """
        if(len(self.goals) == 0):
            yield state
            return

        if(len(self.goals) == 1):
            yield from self.goals[0].run(state)
            return

        anyStreams = True
        goals = self.goals
        goalStreams = [[goals[0].run(state)]] + [[] for i in range(0, len(goals))]
        while anyStreams:
            anyStreams = False
            for goalStreamIndex in range(0, len(goals)):
                newStreams = []
                stateStreams = goalStreams[goalStreamIndex]

                for stateStream in stateStreams:
                    try:
                        nextState = stateStream.__next__()
                        newStreams.append(stateStream)
                        if (goalStreamIndex + 1) == len(goals):
                            yield nextState
                        else:
                            newStream = goals[goalStreamIndex + 1].run(nextState)
                            goalStreams[goalStreamIndex + 1].append(newStream)
                    except StopIteration:
                        pass
                if anyStreams or newStreams:
                    anyStreams = True
                goalStreams[goalStreamIndex] = newStreams
