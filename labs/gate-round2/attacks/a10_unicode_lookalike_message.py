import cachetools

c = cachetools.LRUCache(maxsize=2, getsizeof=int)
c[1] = 'value too large'.replace('e', 'е')
