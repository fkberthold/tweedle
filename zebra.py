import sys
from microkanren.ukanren import *
from microkanren.list import *
import unification

def inordero(left, right, lst):
    isNext = Fresh(lambda rest: Conj(conso(left, rest, lst), Firsto(rest, right)))
    inRest = Fresh(lambda first, rest: Conj(conso(first, rest, lst), inordero(left, right, rest)))
    return Disj(isNext, inRest)

def isnexto(x, y, lst):
    return Disj(inordero(x, y, lst), inordero(y, x, lst))

def indexoIs(index, val, lst):
    if index <= 0:
        return Conj(Firsto(lst, val))
    else:
        return Fresh(lambda rest:
                          Conj(Resto(lst, rest),
                               indexoIs(index - 1, val, rest)))

def deepWalk(term, substitution):
    if isinstance(term, LogicVariable):
        value = substitution.get(term, term)
        if isinstance(value, LogicVariable) and value != term:
            return deepWalk(value, substitution)
        elif isinstance(value, list):
            return deepWalk(value, substitution)
        else:
            return value
    elif isinstance(term, list):
        return [deepWalk(newTerm, substitution) for newTerm in term]
    else:
        return term

def collapse(state):
    newSub = {}
    for key in state.substitution:
        if(key.id == 0):
            newSub[key] = deepWalk(key, state.substitution)
    state.substitution = newSub
    return state

def disp(stream):
    stepCount = 0
    for val in stream:
        print("=========")
        print("Step: %i" % stepCount)
        print((val))
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

(english, swede, dane, norwegian, german) = ("English", "Swede", "Dane", "Norwegian", "German")
(dog, bird, cat, horse, zebra) = ("dog", "bird", "cat", "horse", "zebra")
(red, white, green, yellow, blue) = ("red", "white", "green", "yellow", "blue")
(tea, coffee, milk, beer, water) = ("tea", "coffee", "milk", "beer", "water")
(pallMall, dunhill, blend, blueMaster, prince) = ("Pall Mall", "Dunhill", "Blend", "Blue Master", "Prince")

nati = 0
peti = 1
colori = 2
drinki = 3
brandi = 4

def isHouse(var):
    return Fresh(lambda nationality, pet, color, drink, brand:\
                    Eq(var, [nationality, pet, color, drink, brand]))

def aHouse(street, index1, val1, index2, val2):
    return Fresh(lambda house, holder1, holder2, holder3:\
                      Conj(membero(house, street),\
                           indexoIs(index1, val1, house),\
                           indexoIs(index2, val2, house)))

def neighbors(street, index1, val1, index2, val2):
    return Fresh(lambda house1, house2:
                      Conj(isnexto(house1, house2, street),
                           indexoIs(index1, val1, house1),
                           indexoIs(index2, val2, house2)))

def rule0(street):
    return Fresh(lambda house: Conj(membero(house, street), indexoIs(peti, "zebra", house)))

def rule1(street):
    """1. There are five houses."""
    return Fresh(lambda house0, house1, house2, house3, house4:\
                          Conj(isHouse(house0),\
                               isHouse(house1),\
                               isHouse(house2),\
                               isHouse(house3),\
                               isHouse(house4),\
                               Eq(street, [house0, house1, house2, house3, house4])))

def rule2(street):
    """2. The English man lives in the red house."""
    return aHouse(street, nati, english, colori, red)

def rule3(street):
    """3. The Swede has a dog."""
    return aHouse(street, nati, swede, peti, dog)

def rule4(street):
    """4. The Dane drinks tea."""
    return aHouse(street, nati, dane, drinki, tea)

def rule5(street):
    """5. The green house is immediately to the left of the white house."""
    return Fresh(lambda left, right: Conj(
                      inordero(left, right, street),\
                      indexoIs(colori, green, left),\
                      indexoIs(colori, white, right)))
def rule6(street):
    """6. They drink coffee in the green house."""
    return aHouse(street, drinki, coffee, colori, green)

def rule7(street):
    """7. The man who smokes Pall Mall has birds."""
    return aHouse(street, brandi, pallMall, peti, bird)

def rule8(street):
    """8. In the yellow house they smoke Dunhill."""
    return aHouse(street, colori, yellow, brandi, dunhill)

def rule9(street):
    """9. In the middle house they drink milk."""
    return Fresh(lambda house: Conj(\
                      indexoIs(2, house, street),\
                      indexoIs(drinki, milk, house)))

def rule10(street):
    """10. The Norwegian lives in the first house."""
    return Fresh(lambda house: Conj(\
                      indexoIs(0, house, street),
                      indexoIs(nati, norwegian, house)))

def rule11(street):
    """11. The man who smokes Blend lives in the house next to the house with cats."""
    return neighbors(street, brandi, blend, peti, cat)

def rule12(street):
    """12. In a house next to the house where they have a horse, they smoke Dunhill."""
    return neighbors(street, peti, horse, brandi, dunhill)

def rule13(street):
    """13. The man who smokes Blue Master drinks beer."""
    return aHouse(street, brandi, blueMaster, drinki, beer)

def rule14(street):
    """14. The German smokes Prince."""
    return aHouse(street, nati, german, brandi, prince)

def rule15(street):
    """15. The Norwegian lives next to the blue house."""
    return neighbors(street, nati, norwegian, colori, blue)

def rule16(street):
    """16. They drink water in a house next to the house where they smoke Blend."""
    return neighbors(street, drinki, water, brandi, blend)

rules = Fresh(lambda st:\
                   Conj(rule1(st),
                        rule2(st),
                        rule3(st),
                        rule4(st),
                        rule5(st),
                        rule6(st),
                        rule7(st),
                        rule8(st),
                        rule9(st),
                        rule10(st),
                        rule11(st),
                        rule12(st),
                        rule13(st),
                        rule14(st),
                        rule15(st),
                        rule16(st),
                        rule0(st)))


startState = rules.prerun(State())
print(startState)
print(rules.run(startState).__next__().reify(LogicVariable(0)))


