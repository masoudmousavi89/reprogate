import pickle
from ordered_set import OrderedSet

# protocol 0 is the default on Python 2 (as in the report); protocol 1 fails the same way
print(pickle.loads(pickle.dumps(OrderedSet(), 0)))
