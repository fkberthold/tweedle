
> 'I know what you're thinking about,' said Tweedledum; 'but it isn't so, nohow.'
>
> 'Contrariwise,' continued Tweedledee, 'if it was so, it might be; and if it were so, it would be; but as it isn't, it ain't. That's logic.'

# tweedle

The intent, of this project is to develop a full constraint logic system in Python, and to be able to use it as though it were built natively in Python.

This means it should:
* Work correctly with native Python data types, the current list includes:
  - int
  - string
  - list
  - set
  - dict
* Coding it doesn't feel tacked on, but at least as natural as functional programming in Python.

We're a long way from done, but have several working prototypes both for how a microkanren in Python can feel like native and how a constraint logic system could be implemented.

If you want to come down the rabbit hole with us, take a look.

# Current Progress

## July 5, 2018

We've completed a reasonable implementation of Jason Hemann's constraint based microKanren and discovered a couple limitations.

1. Intermixing constraint and generation removes a lot of the performance gains from a constraint system.
2. Without logical quanitifiers there are several constraints that can lead to either an infinite recurse, or generating non-sense cases indefinitely.

Our task in the coming months will be to design the next phase prototype which will separate constraints and generation.

Also, as of today we'll be releasing this code publicly in the hopes it can help others exploring the same areas.

## April 23, 2018

We've completed a first pass with microkanren without constraints that works reasonably well over lists and dictionaries.  It has macros included that allow for coding with a more Pythonic feel.

We've started work on a constraint microkanren. The current iteration is very closely tied to the design in [A Framework for Extending microKanren with Constraints](https://arxiv.org/pdf/1701.00633), including operating over lisp style data structures.  Once I've solidified the implementation, then I'll work on making it more Pythonic.
