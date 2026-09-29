import ast
from collections import ChainMap

from pure_eval import Evaluator

# Frame locals of a class body whose metaclass __prepare__ returns a list, as in the report.
# Evaluator.from_frame builds ChainMap(frame.f_locals, f_globals, f_builtins); do the same directly.
evaluator = Evaluator(ChainMap([], {}, {}))
node = ast.parse("Y", mode="eval").body
print(evaluator[node])
