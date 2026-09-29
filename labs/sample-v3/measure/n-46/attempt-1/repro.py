import collections, collections.abc
# ordered_set at this commit needs collections.MutableSet (removed in Python 3.10)
collections.MutableSet = collections.abc.MutableSet
import pickle
from ordered_set import OrderedSet

# protocol 0/1 skip __setstate__ for the empty (falsy) state, as Python 2 did by default
print(pickle.loads(pickle.dumps(OrderedSet(), 1)))
