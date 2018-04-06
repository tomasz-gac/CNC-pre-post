from enum import IntEnum, unique
  
@unique
class Arithmetic(IntEnum):
  ADD = 0  # A B ADD -> A + B
  SUB = 1  # A B SUB -> A - B
  MUL = 2  # A B MUL -> A * B
  DIV = 3  # A B DIV -> A / B
  POW = 4  # A B POW -> A ^ B
  LET = 5  # A B LET -> B = A; A
  GET = 7  # A   GET -> A
  
@ev.stack2args(2)
def ADD( state, A, B ):
  return [ A + B ]

@ev.stack2args(2)
def SUB( state, A, B ):
  return [ A - B ]

@ev.stack2args(2)
def MUL( state, A, B ):
  return [ A * B ]

@ev.stack2args(2)
def DIV( state, A, B ):
  return [ A / B ]

@ev.stack2args(2)
def POW( state, A, B ):
  return [ A ** B ]
  
@ev.stack2args(1)
def GET( state, A ):
  try:
    return [ state.symtable[A] ]
  except ( KeyError, AtributeError ):
    raise RuntimeError('Unknown variable : '+str(A))
    
@ev.stack2args(2)
def LET( state, A, B ):
  try:
    state.symtable[A] = B
  except AtributeError:
    state.symtable = { A : B }
  return [ B ]