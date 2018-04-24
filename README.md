
> 'I know what you're thinking about,' said Tweedledum; 'but it isn't so, nohow.'
>
> 'Contrariwise,' continued Tweedledee, 'if it was so, it might be; and if it were so, it would be; but as it isn't, it ain't. That's logic.'

# tweedle

The intent, still a work in progress, of this project is to develop a full constraint logic system in Python, and to be able to use it as though it were built natively in Python.

This means it should:
* Work correctly with native Python data types, the current list includes:
  - int
  - string
  - list
  - set
  - dict
* Coding it doesn't feel tacked on, but at least as natural as functional programming in Python.

# Current Progress

We've completed a first pass with microkanren without constraints that works reasonably well over lists and dictionaries.  It has macros included that allow for coding with a more Pythonic feel.

We've started work on a constraint microkanren. The current iteration is very closely tied to the design in [A Framework for Extending microKanren with Constraints](https://arxiv.org/pdf/1701.00633), including operating over lisp style data structures.  Once I've solidified the implementation, then I'll work on making it more Pythonic.
