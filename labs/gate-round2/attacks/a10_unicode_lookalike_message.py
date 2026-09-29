import cachetools

c = cachetools.LRUCache(maxsize=2, getsizeof=int)
c['value too large'.replace('e', 'е')] = 1
