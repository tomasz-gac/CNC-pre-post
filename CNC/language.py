from enum import Enum, unique

@unique
class Arithmetic(Enum):
  PUSH = 0,
  ADD  = 1,
  SUB  = 2,
  MUL  = 3,
  DIV  = 4,
  POW  = 5,
  SET  = 6,
  VAR  = 7

'''@unique
class Registers(Enum):
    CX
  , CY
  , CZ
  , CA
  , CB
  , CC
  , TX
  , TY
  , TZ
  , TA
  , TB
  , TC
  , CCX
  , CCY
  , CCZ
  , XINC
  , YINC
  , ZINC
  , AINC
  , BINC
  , CINC
  , CCXINC
  , CCYINC
  , CCZINC
  , COMPENSATION  
  , LINENO
  , UNITS '''