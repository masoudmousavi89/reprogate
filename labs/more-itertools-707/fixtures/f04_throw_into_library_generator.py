import more_itertools as mi

gen = mi.iterate(lambda x: x * 2, start=1)
next(gen)
gen.throw(StopIteration)
