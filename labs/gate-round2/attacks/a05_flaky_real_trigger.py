import os
import cachetools

c = cachetools.LRUCache(maxsize=2, missing=lambda x: x, getsizeof=lambda x: x)
print(c[3 if os.urandom(1)[0] % 2 == 0 else 1])
