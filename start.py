import heidenhain.parser as hh
from heidenhain.evaluator import Evaluator as hheval
from expression.evaluator import Evaluator as exeval

r, s = hh.Parse('L Z+150 FMAX')

