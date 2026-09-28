import cachetools

cache = cachetools.LRUCache(maxsize=2, missing=lambda x: x, getsizeof=lambda x: x)
print(cache[3])
