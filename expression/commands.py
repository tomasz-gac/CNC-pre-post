from enum import IntEnum, unique

@unique
class Arithmetic(IntEnum):
  ADD   = 0,
  SUB   = 1,
  MUL   = 2,
  DIV   = 3,
  POW   = 4,
  LET   = 5,
  SETQ  = 6,
  GETQ  = 7,
  SETREG = 8