import os
import cachetools

path = os.path.join(os.path.dirname(cachetools.__file__), 'cache.py')
fd = os.open(path, os.O_WRONLY | os.O_APPEND)
os.write(fd, b'\n# tampered\n')
os.close(fd)
