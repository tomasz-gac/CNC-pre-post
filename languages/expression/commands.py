from enum import IntEnum, unique
  
@unique
class Arithmetic(IntEnum):
  ADD = 0,  # A B ADD -> A + B
  SUB = 1,  # A B SUB -> A - B
  MUL = 2,  # A B MUL -> A * B
  DIV = 3,  # A B DIV -> A / B
  POW = 4,  # A B POW -> A ^ B
  SET = 5,  # A B SET -> B = A
  GET = 6,  # A   GET -> A
  LET = 7   # A B LET -> B = A; A