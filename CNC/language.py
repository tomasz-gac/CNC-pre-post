from enum import Enum, unique

@unique
class Arithmetic(Enum):
  ADD   = 0,
  SUB   = 1,
  MUL   = 2,
  DIV   = 3,
  POW   = 4,
  LET   = 5,
  SETQ  = 6,
  GETQ  = 7

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