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
            return "?%s(%i)" % (self.name, self.id)
        else:
            return "?%i" % self.id

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
<<<<<<< HEAD
        """Unique hash for any given State is needed for some portions of unit testing.
        """
        return hash((self.valid, tuple(self.substitution.keys()), tuple(self.substitution.values())))
=======
        """"""
        return hash((tuple(self.substitution.keys()), tuple(self.substitution.values())))
>>>>>>> collectionTypes

    def __eq__(self, other):
        """Test equality with another state, needed for unit testing.

        @param: Another state object.
        @return: True if valid and substitution match.
        """
        assert isinstance(other, State)
        return self.valid == other.valid and self.substitution == other.substitution

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
        newTerm = term
        while varq(newTerm) and newTerm in self.substitution:
            newTerm = self.substitution[newTerm]
        if isinstance(newTerm, list):
            newTerm = [self.reify(val) for val in newTerm]
            return newTerm
        else:
            return newTerm

mzero = iter([])

def unit(state):
    yield state

class Goal(abc.ABC):
    """A goal is ..."""

    def __init__(self):
        self.lastState = None

    def __and__(self, other):
        return Conj(self, other)

    def __or__(self, other):
        return Disj(self, other)

    @abc.abstractmethod
    def __run__(self, state):
        return

    def run(self, state=State(), results=None):
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
    pass

class Connective(Goal, abc.ABC):
    _goals = []

    @property
    def goals(self):
        return self._goals

    @goals.setter
    def goals(self, goals):
        self._goals = goals

class Eq(Relation):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return "Eq(%s,%s)" % (self.left, self.right)

    def __run__(self, state):
        left = state.reify(self.left)
        right = state.reify(self.right)
        if varq(left) and varq(right) and left.id == right.id:
            yield state.update()
        elif varq(left):
            yield state.ext_s({left: right})
        elif varq(right):
            yield state.ext_s({right: left})
        elif isinstance(left, str):
            if left == right:
                yield state.update()
            else:
                yield state.update(valid=False)
        elif hasattr(left, '__len__') and hasattr(right, '__len__') and len(left) > 0 and len(left) == len(right):
            try: # Dictionary Case
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

                inBoth = leftKeys & rightKeys
                if inBoth:
                    baseGoal = Conj(*[Eq(left[key], right[key]) for key in inBoth])
                else:
                    baseGoal = None

                if leftVars or rightVars:
                    for combinationSet in self.setCombinations(leftVars, rightVars, leftLiterals, rightLiterals):
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
                assert hasattr(left, '__getitem__') and hasattr(right, '__getitem__')
                yield from Conj(*[Eq(leftVal, rightVal) for (leftVal, rightVal) in zip(left, right)]).run(state)
                return
            except Exception as err:
                pass

            try: # Unordered Iterator Case
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
            yield state.update()
        else:
            yield state.update(valid=False)

    def setCombinations(self, leftVars, rightVars, leftLits, rightLits):
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

class Fresh(Goal):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.function_vars = None
        self.goal = None

    def __repr__(self):
        goal = self.getFunctionGoal()
        return "Fresh %s: %s" % (str(self.function_vars), str(type(self.goal)))

    def getFunctionGoal(self):
        if self.goal:
            return self.goal
        else:
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
    def __run__(self, state):
        goal = self.getFunctionGoal()
        for result in goal.run(state):
            reified_state = {}
            for var in self.function_vars:
                reified_state[var] = result.reify(var)
            yield state.update(reified_state)

class Disj(Connective):
    def __init__(self, *goals):
        super().__init__()
        self.goals = list(goals)

    def __repr__(self):
        if self.goals:
            return " | ".join([("(%s)" % str(goal)) if isinstance(goal, Connective) else str(goal) for goal in self.goals])
        else:
            return "DISJ"

    def __run__(self, state):
        goals = self.goals
        stateStreams = [goal.run(state) for goal in goals]
        newStreams = []
        while stateStreams:
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
    def __init__(self, *goals):
        super().__init__()
        self.goals = list(goals)

    def __repr__(self):
        if self.goals:
            return " & ".join([("(%s)" % str(goal)) if isinstance(goal, Connective) else str(goal) for goal in self.goals])
        else:
            return "CONJ"

    def __run__(self, state):
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
