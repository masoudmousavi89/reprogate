from itertools import islice
import more_itertools as mi


def func(num):
    if num > 100:
        raise StopIteration
    return num * 2


print(list(islice(mi.iterate(func, start=1), 10)))
