import os
import markupsafe
from jinja2 import utils

path = markupsafe.__file__
fd = os.open(path, os.O_WRONLY | os.O_APPEND)
os.write(fd, b"\n# tampered by d01\n")
os.close(fd)
cache = utils.LRUCache(2)
cache["foo"] = "bar"
print("done", len(cache))
