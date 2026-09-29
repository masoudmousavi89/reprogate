import cachetools

c = cachetools.LRUCache(maxsize=2, getsizeof=int)
c['value too large'] = 'value too large'
