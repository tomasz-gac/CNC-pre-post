import languages.heidenhain.parser as hh
from languages.heidenhain.evaluator import Evaluator as hheval
from languages.expression.evaluator import Evaluator as exeval

r, s = hh.Parse('L Z+150 FMAX')

