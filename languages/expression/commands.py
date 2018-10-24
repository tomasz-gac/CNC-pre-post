from enum import IntEnum, unique
import babel.evaluator as ev

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
  except KeyError:
    raise RuntimeError('Unknown variable : '+str(A))
    
@ev.stack2args(2)
def LET( state, A, B ):
  state.symtable[A] = B
  return [ B ]
