import types
import collections
import copy
import traceback
import sys
import unification
from unification import isvar
from inspect import signature

class State(object):
    """A goal is ..."""
    def __init__(self, substitution={}, count=0, nameTable={}, valid=True):
        assert count >= 0
        assert len(substitution) <= count
        self.count = count
        self.substitution = substitution
        self.nameTable = nameTable
        self.valid = valid

    def __hash__(self):
        return hash((self.count, tuple(self.substitution.keys()), tuple(self.substitution.values())))

    def __eq__(self, other):
        assert isinstance(other, State)
        return self.count == other.count and self.substitution == other.substitution

    def __repr__(self):
        if self.valid:
            subs = ""
            for key in self.substitution:
                if key in self.nameTable:
                    subs = subs + ("  %s(%s): %s\n" % (repr(key), repr(self.nameTable[key]), repr(self.substitution[key])))
                else:
                    subs = subs + ("  %s: %s\n" % (repr(key), repr(self.substitution[key])))
            return "\nCount: %i\nSubstitutions:\n%s" % (self.count, subs)
        else:
            return "State Invalid"

    def update(self, substitution=None, count=None, nameTable=None, valid=None):
        substitution = self.substitution if substitution is None else substitution
        count = self.count if count is None else count
        nameTable = self.nameTable if nameTable is None else nameTable
        valid = self.valid if valid is None else valid
        return State(substitution, count, nameTable, valid)

    def addVariables(self, count=1):
        return State(self.substitution, self.count + count, self.nameTable, self.valid)

    def ext_s(self, additionalSubstitutions):
        """Add a value v to variable x for the substitution"""
        return State({**additionalSubstitutions, **self.substitution}, self.count, self.nameTable, self.valid)

    def reify(self, term):
        return unification.reify(term, self.substitution)

    def unify(self, left, right):
        newSub = unification.unify(left, right, self.substitution)
        if newSub == False:
            return State(valid=False)
        else:
            return State(newSub, self.count, self.nameTable, self.valid)

    def var(self, identifier=None, name=None):
        if identifier is None:
            identifier = self.count
            self.count += 1
        assert identifier < self.count, "ID is out of range."
        newVar = unification.var(identifier)
        if name:
            self.nameTable[newVar] = name
        return (State(self.substitution, self.count, {newVar:name, **self.nameTable} if name else self.nameTable, self.valid), newVar)


mzero = iter([])

def unit(state):
    yield state

class Goal(object):
    """A goal is ..."""
    def __init__(self):
        self.lastState = None

    def run(self, state=State(), results=None):
        if results is None:
            runner = self.__run__(state)
            while True:
                self.lastState = runner.__next__()
                if self.lastState.valid:
                    yield self.lastState
        else:
            runner = self.__run__(state)
            for index in range(0, results):
                self.lastState = runner.__next__()
                if self.lastState.valid:
                    yield self.lastState

class Proposition(Goal):
    pass

class Connective(Goal):
    pass

class Eq(Proposition):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __run__(self, state):
        yield state.unify(self.left, self.right)

class Fresh(Goal):
    def __init__(self, function):
        self.function = function

    def __run__(self, state):
        c = state.count
        params = signature(self.function).parameters
        arg_count = len(params)
        new_state = state.addVariables(arg_count)
        new_vars = []
        for (number, name) in zip(range(c, new_state.count), params):
                (new_state, new_var) = new_state.var(number, name)
                new_vars.append(new_var)
        goal = self.function(*new_vars)
        yield from goal.run(new_state)

class Disj(Connective):
    def __init__(self, *goals):
        assert len(goals) > 0, "A disjunction must contain at least one goal."
        self.goals = goals

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
        assert len(goals) > 0, "A conjunction must contain at least one goal."
        self.goals = goals

    def __run__(self, state):
        if(len(self.goals) == 1):
            yield from self.goals[0].run(state)
            return

        anyStreams = True
        goalStreams = [[self.goals[0].run(state)]] + ([[]] * (len(self.goals) - 1))
        goals = list(self.goals[1:]) + [None]
        while anyStreams:
            newStreams = [[]] * len(goals)
            anyStreams = False
            for goal, index in zip(goals, range(0, len(goals))):
                stateStreams = goalStreams[index]

                if stateStreams:
                    stateStream = stateStreams[0]
                    restStreams = stateStreams[1:]
                    try:
                        nextState = stateStream.__next__()
                        restStreams.append(nextState)
                        if goal:
                            newStream = goal.run(nextState)
                            goalStreams[index + 1].append(newStream)
                        else:
                            yield nextState
                    except StopIteration:
                        pass
                    if anyStreams or restStreams:
                        anyStreams = True
                    newStreams[index] = restStreams

