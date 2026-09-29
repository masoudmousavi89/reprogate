import operator
from cachetools import LRUCache, cachedmethod


class Cached(object):
    def __init__(self, cache):
        self.cache = cache

    @cachedmethod(operator.attrgetter('cache'))
    def get(self, value):
        return value


print(Cached(LRUCache(maxsize=0)).get(1))
