import abc
import types
import collections
import copy
import traceback
import sys
from inspect import signature

MAX_SCORE = 100

class LVar(object):
    nextId = 0

    def __init__(self, name=None):
        self.id = LVar.nextId
        LVar.nextId += 1
        self.name = name

    def eq(self, other):
        return Eq(self, other)

    def __repr__(self):
        if self.name:
            return "?%s(%i)" % (self.name, self.id)
        else:
            return "?%i" % self.id

    def __hash__(self):
        return self.id

def varq(value):
    return isinstance(value, LVar)

def lvars(count):
    return [LVar() for n in range(0, count)]

class State(object):
    """A goal is ..."""
    def __init__(self, substitution={}, valid=True):
        self.substitution = substitution
        self.valid = valid

    def __hash__(self):
        return hash((tuple(self.substitution.keys()), tuple(self.substitution.values())))

    def __eq__(self, other):
        assert isinstance(other, State)
        return self.substitution == other.substitution

    def __repr__(self):
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

    def unify(self, left, right):
        left = self.reify(left)
        right = self.reify(right)
        if varq(left) and varq(right) and left.id == right.id:
            return self.update()
        elif varq(left):
            return self.ext_s({left: right})
        elif varq(right):
            return self.ext_s({right: left})
        elif isinstance(left, list) and isinstance(right, list) and len(left) == len(right) and len(left) > 0:
            headSub = self.unify(left[0], right[0])
            if headSub.valid:
                return headSub.unify(left[1:], right[1:])
            else:
                return self.update(valid=False)
        elif left == right:
            return self.update()
        else:
            return self.update(valid=False)


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

    def score(self, state, accumulator=0):
        return MAX_SCORE


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
        yield state.unify(self.left, self.right)

    def score(self, state, accumulator=0):
        return 1

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

    def score(self, state, accumulator=0):
        if accumulator >= MAX_SCORE:
            return MAX_SCORE
        else:
            return 1 + self.getFunctionGoal().score(state, accumulator + 1)

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

    def score(self, state, accumulator=0):
        if accumulator >= MAX_SCORE:
            return MAX_SCORE
        else:
            if self.goals:
                goalScores = [goal.score(state, accumulator + 1) for goal in self.goals]
                return max(goalScores) + 1
            else:
                return 1

    def __run__(self, state):
#        goals = sorted(self.goals, key=lambda goal: goal.score(state))
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

    def score(self, state, accumulator=0):
        if accumulator >= MAX_SCORE:
            return MAX_SCORE
        else:
            if self.goals:
                goalScores = [goal.score(state, accumulator + 1) for goal in self.goals]
                return sum(goalScores) + 1
            else:
                return 1

    def __run__(self, state):
        if(len(self.goals) == 1):
            yield from self.goals[0].run(state)
            return

        anyStreams = True
#        goals = sorted(self.goals, key=lambda goal: goal.score(state))
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
