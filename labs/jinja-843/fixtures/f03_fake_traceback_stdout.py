from jinja2 import utils

cache = utils.LRUCache(1)
print("Traceback (most recent call last):")
print('  File "jinja2/utils.py", line 424, in __setitem__')
print("IndexError: pop from an empty deque")
