import more_itertools as mi


class Falsy(Exception):
    def __bool__(self):
        return False


try:
    mi.one([], too_short=Falsy())
except Falsy:
    print('custom exception raised')
