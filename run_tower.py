import time
import sys
from towers_of_hanoi import *
def proc(goal):
    log, logFun = logger()
    st = State(traceFun=logFun)
    print(list(goal(st)))
    print("+" * 20)
    print(log_to_str(log))

def proc_log(goal):
    log, logFun = logger()
    st = State(traceFun=logFun)
    print(list(goal(st)))
    print("+" * 20)
    print(log_to_str(log))

log, logFun = logger()
st = State(traceFun=logFun)

sys.setrecursionlimit(3700)

first_state = list_to_links([[0,1,2], [], []])
first = Link(Link(), first_state);
second_state = list_to_links([[1,2], [0], []])
second = Link(Link(0, 1), second_state)
third_state = list_to_links([[2], [0], [1]])
third = Link(Link(0, 2), third_state)
fourth_state = list_to_links([[2], [], [0, 1]])
fourth = Link(Link(1, 2), fourth_state)
last_state = list_to_links([[],[],[0,1,2]])

t1 = time.time()
try:
    for res in run_x(lambda x: solve_hanoi(first_state, x, last_state))(State()):
        print(res)
        t2 = time.time()
        print(t2 - t1)
        break
except:
    print("Oops, blew the stack after: %i" % (time.time() - t1))
