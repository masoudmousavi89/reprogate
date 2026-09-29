import collections
import collections.abc
import pickle

# The project (2015 code) needs collections.MutableSet, removed in Python 3.10.
collections.MutableSet = collections.abc.MutableSet
collections.Sequence = collections.abc.Sequence

from ordered_set import OrderedSet

# Python 2 default pickle protocol is 0 (the empty-list state is dropped there too).
print(pickle.loads(pickle.dumps(OrderedSet(), protocol=0)))
