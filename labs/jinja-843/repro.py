from jinja2 import utils

cache = utils.LRUCache(1)
cache['foo'] = 'bar'
copy = cache.copy()
copy['blah'] = 'blargh'
print("OK, keys:", list(copy.keys()))
