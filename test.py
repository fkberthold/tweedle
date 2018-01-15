import os.path
import sys
import unittest
import time
from microkanren.urkanren import *
from microkanren.list import *

empty = State()

def inordero(left, right, lst):
    isNext = call_fresh(lambda tail: conj(conso(left, tail, lst), firsto(tail, right)))
    inRest = call_fresh(lambda first, tail: conj(conso(first, tail, lst), nexto(left, right, tail)))
    return disj(isNext, inRest)

def isnexto(x, y, lst):
    return disj(inordero(x, y, lst), inordero(y, x, lst))

def indexoIs(index, val, lst):
    if index <= 0:
        return conj(firsto(lst, val))
    else:
        return call_fresh(lambda tail:
                          conj(tailo(lst, tail),
                               indexoIs(index - 1, val, tail)))

#def oneOf(member, rest, lst):
#    justOne = conj(eq(rest, []),
#                   conso(member, [], lst))
#    takeOne = conj(firsto(lst, member),
#                   ))

def notEq(left, right):
    def notEqHelp(state):
        unified = unify(left, right, state.substitution)
        if isinstance(unified, dict):
            return mzero
        else:
            return unit(state)
    return generate(notEqHelp)

def collapse(state):
    newSub = {}
    for key in state.substitution:
        base = state.substitution[key]
        newSub[key] = walk(base, state.substitution)
    state.substitution = newSub
    return state

def disp(stream):
    stepCount = 0
    for val in stream:
        print("=========")
        print("Step: %i" % stepCount)
        print(val)
        stepCount = stepCount + 1
        sys.stdout.flush()

"""
The Zebra puzzle, a.k.a. Einstein's Riddle, is a logic puzzle which is to be solved programmatically. 
It has several variants, one of them this:

1. There are five houses.
2. The English man lives in the red house.
3. The Swede has a dog.
4. The Dane drinks tea.
5. The green house is immediately to the left of the white house.
6. They drink coffee in the green house.
7. The man who smokes Pall Mall has birds.
8. In the yellow house they smoke Dunhill.
9. In the middle house they drink milk.
10. The Norwegian lives in the first house.
11. The man who smokes Blend lives in the house next to the house with cats.
12. In a house next to the house where they have a horse, they smoke Dunhill.
13. The man who smokes Blue Master drinks beer.
14. The German smokes Prince.
15. The Norwegian lives next to the blue house.
16. They drink water in a house next to the house where they smoke Blend.

The question is, who owns the zebra?"""

nationalities = ["English", "Swede", "Dane", "Norwegian", "German"]
pets = ["dog", "bird", "cat", "horse", "zebra"]
colors = ["red", "white", "green", "yellow", "blue"]
drinks = ["tea", "coffee", "milk", "beer", "water"]
brands = ["Pall Mall", "Dunhill", "Blend", "Blue Master", "Prince"]
properties = [nationalities, pets, colors, drinks, brands]

nati = 0
peti = 1
colori = 2
drinki = 3
brandi = 4
posi = 5

def lHouse(var, pos):
    return call_fresh(lambda nationality:\
                   conj(membero(nationality, nationalities),
                        eq(var, [nationality, pos])))

def lrule0(street):
    """1. There are five houses."""
    return call_fresh(lambda house1, house2:\
                          conj(lHouse(house1, 0),\
                               lHouse(house2, 1),
                               eq(street, [house1, house2])))
def lrule1(street):
    def ine(index):
        return call_fresh(lambda house1, val1, pos1, house2, val2, pos2:
                      conj(indexoIs(1, pos1, house1),
                           indexoIs(1, pos2, house2),
                           eq(pos1, pos2),
                           indexoIs(index, val1, house1),
                           indexoIs(index, val2, house2),
                           eq(val1, val2)))
    return conj(ine(0))

lrules = call_fresh(lambda st:\
                    conj(lrule0(st), lrule1(st)))

disp(lrules(empty))

def isHouse(var, pos):
    return call_fresh(lambda nationality, pet, color, drink, brand:\
                   conj(membero(nationality, nationalities),\
                        membero(pet, pets),\
                        membero(color, colors),\
                        membero(drink, drinks),\
                        membero(brand, brands),\
                        eq(var, [nationality, pet, color, drink, brand, pos])))

def aHouse(street, index1, val1, index2, val2):
    return call_fresh(lambda house:\
                      conj(membero(house, street),\
                           indexoIs(index1, val1, house),\
                           indexoIs(index2, val2, house)))

def neighbors(street, index1, val1, index2, val2):
    return call_fresh(lambda house1, house2:
                      conj(isnexto(house1, house2, street),
                           indexoIs(index1, val1, house1),
                           indexoIs(index2, val2, house2)))

def rule1(street):
    def ine(index):
        return call_fresh(lambda house1, val1, pos1, house2, val2, pos2:
                      conj(indexoIs(posi, pos1, house1),
                           indexoIs(posi, pos2, house2),
                           notEq(pos1, pos2),
                           indexoIs(index, val1, house1),
                           indexoIs(index, val2, house2),
                           notEq(val1, val2)))
    return conj(ine(0), ine(1), ine(2), ine(3), ine(4))

def rule0(street):
    """1. There are five houses."""
    return call_fresh(lambda house1, house2, house3, house4, house5:\
                          conj(isHouse(house1, 0),\
                               isHouse(house2, 1),\
                               isHouse(house3, 2),\
                               isHouse(house4, 3),\
                               isHouse(house5, 4),\
                               eq(street, [house1, house2, house3, house4, house5])))

def rule2(street):
    """2. The English man lives in the red house."""
    return aHouse(street, nati, "English", colori, "red")

def rule3(street):
    """3. The Swede has a dog."""
    return aHouse(street, nati, "Swede", peti, "dog")

def rule4(street):
    """4. The Dane drinks tea."""
    return aHouse(street, nati, "Dane", drinki, "tea")

def rule5(street):
    """5. The green house is immediately to the left of the white house."""
    return call_fresh(lambda left, right: conj(
                      inordero(left, right, street),\
                      indexoIs(colori, "green", left),\
                      indexoIs(colori, "white", right)))
def rule6(street):
    """6. They drink coffee in the green house."""
    return aHouse(street, drinki, "coffee", colori, "green")

def rule7(street):
    """7. The man who smokes Pall Mall has birds."""
    return aHouse(street, brandi, "Pall Mall", peti, "bird")

def rule8(street):
    """8. In the yellow house they smoke Dunhill."""
    return aHouse(street, colori, "yellow", brandi, "Dunhill")

def rule9(street):
    """9. In the middle house they drink milk."""
    return call_fresh(lambda house: conj(\
                      indexoIs(2, house, street),\
                      indexoIs(drinki, "milk", house)))

def rule10(street):
    """10. The Norwegian lives in the first house."""
    return call_fresh(lambda house: conj(\
                      indexoIs(0, house, street),
                      indexoIs(nati, "Norwegian", house)))

def rule11(street):
    """11. The man who smokes Blend lives in the house next to the house with cats."""
    return neighbors(street, brandi, "Blend", peti, "cat")

def rule12(street):
    """12. In a house next to the house where they have a horse, they smoke Dunhill."""
    return neighbors(street, brandi, "Dunhill", peti, "horse")

def rule13(street):
    """13. The man who smokes Blue Master drinks beer."""
    return aHouse(street, brandi, "Blue Master", drinki, "beer")

def rule14(street):
    """14. The German smokes Prince."""
    return aHouse(street, nati, "German", brandi, "Prince")

def rule15(street):
    """15. The Norwegian lives next to the blue house."""
    return neighbors(street, nati, "Norwegian", colori, "blue")

def rule16(street):
    """16. They drink water in a house next to the house where they smoke Blend."""
    return neighbors(street, drinki, "water", brandi, "Blend")

rules = call_fresh(lambda st:\
                   conj(rule0(st),\
                        rule1(st)))
#                        rule2(st),
#                        rule3(st),
#                        rule4(st),
#                        rule5(st),
#                        rule6(st),
#                        rule7(st),
#                        rule8(st),
#                        rule9(st),
#                        rule10(st),
#                        rule11(st),
#                        rule12(st),
#                        rule13(st),
#                        rule14(st),
#                        rule15(st),
#                        rule16(st)))

#disp(call_fresh(lambda left, right, lst, tail: conso(left, tail, [1,2,3,4]))(empty))
#ls = ['a', 'b', 'c', 'd', 'e']
#disp(call_fresh(lambda x, y: conj(membero(x, ls), membero(y, ls)))(empty))
#disp(rules(empty))

