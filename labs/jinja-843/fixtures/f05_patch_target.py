from collections import deque
from jinja2 import utils


def boom(self, key, value):
    deque().popleft()


utils.LRUCache.__setitem__ = boom
cache = utils.LRUCache(1)
cache['foo'] = 'bar'
