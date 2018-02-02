import abc
import types
import collections
import copy
import traceback
import sys
from inspect import signature

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

    def addVariables(self, count=1):
        return self

    def ext_s(self, additionalSubstitutions):
        """Add a value v to variable x for the substitution"""
        return self.update(substitution={**additionalSubstitutions, **self.substitution})

    def reify(self, term):
        while varq(term) and term in self.substitution:
            term = self.substitution[term]
        if isinstance(term, list):
            term = [self.reify(val) for val in term]
        return term

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

    def var(self, identifier=None, name=None):
        if identifier is None:
            nextState = self.addVariables(1)
        else:
            nextState = State(self.substitution, [], self.valid)
        newVar = LVar(name)
        return (nextState, newVar)

    def vars(self, count):
        nextState = self.addVariables(count)
        newVars = [LVar() for identifier in range(count)]
        return (nextState, newVars)


mzero = iter([])

def unit(state):
    yield state

class Goal(abc.ABC):
    """A goal is ..."""

    def __init__(self):
        self.lastState = None
        self.hasPrerun = False
        layer = Connective.currentLayer()
        if(layer):
            layer.goals.append(self)

    def __and__(self, other):
        return Conj(self, other)

    def __or__(self, other):
        return Disj(self, other)

    def prerun(self, state):
        self.hasPrerun = True
        return self.__prerun__(state)

    def __prerun__(self, state):
        return state

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
    _layers = []
    _goals = []

    @classmethod
    def register(cls, connective):
        cls._layers.append(connective)

    @classmethod
    def currentLayer(cls):
        if cls._layers:
            return cls._layers[-1]
        else:
            return None

    @classmethod
    def unregister(cls):
        return cls._layers.pop()

    @property
    def goals(self):
        return self._goals

    @goals.setter
    def goals(self, goals):
        self._goals = goals

    def __enter__(self):
        Connective.register(self)
        return self

    def __exit__(self, *args):
        Connective.unregister()

class Eq(Relation):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return "Eq(%s,%s)" % (self.left, self.right)

    def __prerun__(self, state):
        return state.unify(self.left, self.right)

    def __run__(self, state):
        yield state.unify(self.left, self.right)

class Fresh(Goal):
    def __init__(self, function):
        super().__init__()
        self.function = function

    def __prerun__(self, state):
        params = signature(self.function).parameters
        arg_count = len(params)
        (new_state, self.new_vars) = state.vars(arg_count)
        for (var, name) in zip(self.new_vars, params):
            var.name = name
        self.goal = self.function(*self.new_vars)
        return self.goal.prerun(new_state)

    def __run__(self, state):
        if self.hasPrerun:
            yield from self.goal.run(state)
        else:
            params = signature(self.function).parameters
            arg_count = len(params)
            (new_state, new_vars) = state.vars(arg_count)
            for (var, name) in zip(new_vars, params):
                var.name = name
            self.goal = self.function(*new_vars)
            yield from self.goal.run(new_state)

class WithFresh(Connective):
    def __init__(self, howMany):
        super().__init__()
        self.howMany = howMany
        self.args = [LVar() for count in range(self.howMany)]

    def __enter__(self):
        super().__enter__()
        return self

    def __iter__(self):
        for val in self.args:
            yield val

    def __repr__(self):
        if self.goals:
            return ("Fresh (%i): " % self.howMany) + " & ".join([str(goal) for goal in self.goals])
        else:
            return "Fresh"

    def __prerun__(self, state):
        self.conj = Conj(*self.goals)
        return self.conj.prerun(state)

    def __run__(self, state):
        if self.hasPrerun:
            yield from self.conj.run(state)
        else:
            yield from Conj(*self.goals).run(state)

class Call(Fresh):
    def __run__(self, state):
        if self.hasPrerun:
            for result in self.goal.run(state):
                reified_sub = {}
                for var in self.new_vars:
                    reified_sub[var] = result.reify(var)
                yield state.update(substitution=reified_sub)
        else:
            params = signature(self.function).parameters
            arg_count = len(params)
            (new_state, new_vars) = state.vars(arg_count)
            for (var, name) in zip(new_vars, params):
                var.name = name
            self.goal = self.function(*new_vars)
            for result in self.goal.run(new_state):
                reified_state = {}
                for var in new_vars:
                    reified_state[var] = result.reify(var)
                yield reified_state


class Disj(Connective):
    def __init__(self, *goals):
        super().__init__()
        self.goals = list(goals)

#    def __prerun__(self, state):
#        for goal in self.goals:
#            new_state = goal.prerun(state)
#            if new_state.valid:
#                return state
#        return state.update(valid=False)

    def __repr__(self):
        if self.goals:
            return " | ".join([str(goal) for goal in self.goals])
        else:
            return "DISJ"

    def __run__(self, state):
        stateStreams = [goal.run(state) for goal in self.goals]
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
            return " & ".join([str(goal) for goal in self.goals])
        else:
            return "CONJ"

    def __prerun__(self, state):
        new_state = state
        for goal in self.goals:
            new_state = goal.prerun(new_state)
            if not new_state.valid:
                return new_state
        return new_state

    def __run__(self, state):
        if(len(self.goals) == 1):
            yield from self.goals[0].run(state)
            return

        anyStreams = True
        goalStreams = [[self.goals[0].run(state)]] + [[] for i in range(0, len(self.goals))]
        while anyStreams:
            anyStreams = False
            for goalStreamIndex in range(0, len(self.goals)):
                newStreams = []
                stateStreams = goalStreams[goalStreamIndex]

                for stateStream in stateStreams:
                    try:
                        nextState = stateStream.__next__()
                        newStreams.append(stateStream)
                        if (goalStreamIndex + 1) == len(self.goals):
                            yield nextState
                        else:
                            newStream = self.goals[goalStreamIndex + 1].run(nextState)
                            goalStreams[goalStreamIndex + 1].append(newStream)
                    except StopIteration:
                        pass
                if anyStreams or newStreams:
                    anyStreams = True
                goalStreams[goalStreamIndex] = newStreams

