import more_itertools as mi

next(iter([]).__iter__()) if False else (_ for _ in ()).throw(RuntimeError('generator raised StopIteration'))
