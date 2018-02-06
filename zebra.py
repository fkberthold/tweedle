import sys
from microkanren.ukanren import *
from microkanren.list import *
import unification

def inordero(left, right, lst):
    inFirst = Fresh(lambda rest: conso(left, rest, lst) & firsto(rest, right))
    inRest = Fresh(lambda first, rest: conso(first, rest, lst) & inordero(left, right, rest))
    return inFirst | inRest

def isnexto(x, y, lst):
    return inordero(x, y, lst) | inordero(y, x, lst)

def indexoIs(index, val, lst):
    if index <= 0:
        return Conj(firsto(lst, val))
    else:
        return Fresh(lambda rest:
                          Conj(resto(lst, rest),
                               indexoIs(index - 1, val, rest)))


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

def aHouse(street, nationality=None, pet=None, color=None, drink=None, brand=None):
    nationality = nationality or LVar()
    pet = pet or LVar()
    color = color or LVar()
    drink = drink or LVar()
    brand = brand or LVar()
    return membero([nationality, pet, color, drink, brand], street)

def neighbors(street, nationality1=None, pet1=None, color1=None, drink1=None, brand1=None,
                    nationality2=None, pet2=None, color2=None, drink2=None, brand2=None):
    nationality1 = nationality1 or LVar()
    pet1 = pet1 or LVar()
    color1 = color1 or LVar()
    drink1 = drink1 or LVar()
    brand1 = brand1 or LVar()
    nationality2 = nationality2 or LVar()
    pet2 = pet2 or LVar()
    color2 = color2 or LVar()
    drink2 = drink2 or LVar()
    brand2 = brand2 or LVar()
    house1 = [nationality1, pet1, color1, drink1, brand1]
    house2 = [nationality2, pet2, color2, drink2, brand2]
    return Conj(isnexto(house1, house2, street))

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
    return aHouse(street, nationality=english, color=red)

def rule3(street):
    """3. The Swede has a dog."""
    return aHouse(street, nationality=swede, pet=dog)

def rule4(street):
    """4. The Dane drinks tea."""
    return aHouse(street, nationality=dane, drink=tea)

def rule5(street):
    """5. The green house is immediately to the left of the white house."""
    return Fresh(lambda left, right: Conj(
                      inordero(left, right, street),\
                      indexoIs(colori, green, left),\
                      indexoIs(colori, white, right)))

def rule6(street):
    """6. They drink coffee in the green house."""
    return aHouse(street, drink=coffee, color=green)

def rule7(street):
    """7. The man who smokes Pall Mall has birds."""
    return aHouse(street, brand=pallMall, pet=bird)

def rule8(street):
    """8. In the yellow house they smoke Dunhill."""
    return aHouse(street, color=yellow, brand=dunhill)

def rule9(street):
    """9. In the middle house they drink milk."""
    return Fresh(lambda house: Conj(\
                      indexoIs(2, house, street),\
                      indexoIs(drinki, milk, house)))

def rule10(street):
    """10. The Norwegian lives in the first house."""
    return Fresh(lambda house: Conj(\
                      firsto(street, house),
                      indexoIs(nati, norwegian, house)))

def rule11(street):
    """11. The man who smokes Blend lives in the house next to the house with cats."""
    return neighbors(street, brand1=blend, pet2=cat)

def rule12(street):
    """12. In a house next to the house where they have a horse, they smoke Dunhill."""
    return neighbors(street, pet1=horse, brand2=dunhill)

def rule13(street):
    """13. The man who smokes Blue Master drinks beer."""
    return aHouse(street, brand=blueMaster, drink=beer)

def rule14(street):
    """14. The German smokes Prince."""
    return aHouse(street, nationality=german, brand=prince)

def rule15(street):
    """15. The Norwegian lives next to the blue house."""
    return neighbors(street, nationality1=norwegian, color2=blue)

def rule16(street):
    """16. They drink water in a house next to the house where they smoke Blend."""
    return neighbors(street, drink1=water, brand2=blend)

rules = Call(lambda st:\
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

#ruleTest = Call(lambda st: rule1(st) & rule15(st))
tst = Call(lambda a: inordero(1, 2, a) & Eq(a, [LVar(), LVar(), LVar()]))

for (c, s) in zip(range(10), tst.run()):
    print(s)
#print(ruleTest.run(State()).__next__())
