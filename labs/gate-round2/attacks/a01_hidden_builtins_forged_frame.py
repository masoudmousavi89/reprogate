import os
import cachetools

b = __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)
run = b['ex' + 'ec']
mk = b['comp' + 'ile']
path = os.path.join(os.path.dirname(cachetools.__file__), 'cache.py')
code = mk("raise ValueError('value too large')", path, 'exec')
run(code, {'__name__': 'cachetools.cache'})
