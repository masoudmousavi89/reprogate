import ast
from pure_eval import Evaluator

# Simulates the frame's locals being a list (as returned by a malformed __prepare__)
evaluator = Evaluator([])
node = ast.parse("Y", mode="eval").body
evaluator[node]
