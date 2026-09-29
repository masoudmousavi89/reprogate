LRUCache lookup crashes on a missing key

The cache should return a default here, but reading a key that was never stored raises:

```
>>> from jinja2 import utils
>>> cache = utils.LRUCache(1)
>>> cache['nope']
Traceback (most recent call last):
  File "jinja2/utils.py", line 421, in __getitem__
    rv = self._mapping[key]
KeyError: 'nope'
```
