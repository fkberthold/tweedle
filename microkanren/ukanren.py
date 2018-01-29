import types
import collections
import copy
import traceback
import sys
from inspect import signature

class LogicVariable(object):
    def __init__(self, identifier, name=None):
        self.id = identifier
        self.name = name

    def __eq__(self, other):
        return isinstance(other, LogicVariable) and self.id == other.id

    def __repr__(self):
        if self.name:
            return "?%s(%i)" % (self.name, self.id)
        else:
            return "?%i" % self.id

    def __hash__(self):
        return self.id

def varq(value):
    return isinstance(value, LogicVariable)


class State(object):
    """A goal is ..."""
    updateCounter = 0
    def __init__(self, substitution={}, count=0, varQueue=None, valid=True):
        assert count >= 0
        assert len(substitution) <= count, "len(substitution) = %i, count = %i" % (len(substitution), count)
        self.count = count
        self.substitution = substitution
        self.valid = valid
        self.varQueue = varQueue

    def __hash__(self):
        return hash((self.count, tuple(self.substitution.keys()), tuple(self.substitution.values())))

    def __eq__(self, other):
        assert isinstance(other, State)
        return self.count == other.count and self.substitution == other.substitution

    def __repr__(self):
        if self.valid:
            subs = ""
            for key in self.substitution:
                subs = subs + ("  %s: %s\n" % (repr(key), repr(self.substitution[key])))
            return "\nCount: %i\nSubstitutions:\n%s" % (self.count, subs)
        else:
            return "State Invalid"

    def update(self, substitution=None, count=None, valid=None):
#        State.updateCounter += 1
        if valid == False:
            return State({}, 0, valid=False)
        else:
            substitution = copy.copy(self.substitution) if substitution is None else substitution
            for (var, value) in self.varQueue if self.varQueue else []:
                substitution[var] = value
            count = self.count if count is None else count
            valid = self.valid if valid is None else valid
            return State(substitution, count, None, valid)

    def addVariables(self, count=1):
        return State(self.substitution, count=self.count + count, varQueue=self.varQueue if self.varQueue else [], valid=self.valid)

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
        if varq(left) and varq(right) and left == right:
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
            identifier = self.count
            nextState = self.addVariables(1)
        else:
            nextState = State(self.substitution, self.count, [], self.valid)
        assert identifier < nextState.count, "count: %i identifier: %i" % (nextState.count, identifier)
        newVar = LogicVariable(identifier, name)
        return (nextState, newVar)

    def vars(self, count):
        nextState = self.addVariables(count)
        newVars = [LogicVariable(identifier) for identifier in range(self.count, self.count + count)]
        return (nextState, newVars)


mzero = iter([])

def unit(state):
    yield state

class Goal(object):
    """A goal is ..."""
    def __init__(self):
        self.lastState = None
        self.hasPrerun = False

    def prerun(self, state):
        self.hasPrerun = True
        return self.__prerun__(state)

    def __prerun__(self, state):
        return state

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


class Proposition(Goal):
    pass

class Connective(Goal):
    pass

class Eq(Proposition):
    def __init__(self, left, right):
        super(Eq, self).__init__()
        self.left = left
        self.right = right

    def __prerun__(self, state):
        return state.unify(self.left, self.right)

    def __run__(self, state):
        yield state.unify(self.left, self.right)

class Fresh(Goal):
    def __init__(self, function):
        super(Fresh, self).__init__()
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

class Disj(Connective):
    def __init__(self, *goals):
        super(Disj, self).__init__()
        assert len(goals) > 0, "A disjunction must contain at least one goal."
        self.goals = goals

#    def __prerun__(self, state):
#        for goal in self.goals:
#            new_state = goal.prerun(state)
#            if new_state.valid:
#                return state
#        return state.update(valid=False)

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
        super(Conj, self).__init__()
        assert len(goals) > 0, "A conjunction must contain at least one goal."
        self.goals = goals

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

