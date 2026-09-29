import ast
from pure_eval import Evaluator

# Frame locals of a class body whose metaclass __prepare__ returns a list.
evaluator = Evaluator([])
node = ast.parse("x").body[0].value
print(evaluator[node])
