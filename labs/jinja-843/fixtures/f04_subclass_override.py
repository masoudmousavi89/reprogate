from collections import deque
from jinja2 import utils


class Sneaky(utils.LRUCache):
    def __setitem__(self, key, value):
        deque().popleft()


cache = Sneaky(1)
cache['foo'] = 'bar'
