from enum import Enum, unique

@unique
class GOTOtokens(Enum):
  linear    = "L(P)?"
  circular  = "C(P)?"

@unique
class ToolCallTokens(Enum):
  DR = 'DR\\s*='
  DL = 'DL\\s*='
  S  = 'S'

@unique
class CoordinateTokens(Enum):
  X = "(I)?(X)"
  Y = "(I)?(Y)"
  Z = "(I)?(Z)"
  A = "(I)?(A)"
  B = "(I)?(B)"
  C = "(I)?(C)"
  PA = "(I)?(P)(A)"
  PR = "(I)?(P)(R)"