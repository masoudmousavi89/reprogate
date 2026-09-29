import cachetools

c = cachetools.LRUCache(maxsize=2, getsizeof=lambda v: v)
try:
    c[3] = 3
except ValueError:
    int('value too large')
