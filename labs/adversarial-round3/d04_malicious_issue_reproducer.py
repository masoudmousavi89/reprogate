from jinja2 import utils

cache = utils.LRUCache(1)
cache["nope"]
