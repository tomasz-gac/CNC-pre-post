from enum import IntEnum, unique
import generator.evaluator as ev
 
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
  symtable = state['symtable']
  try:
    return [ symtable[A] ]
  except KeyError:
    raise RuntimeError('Unknown variable : '+str(A))
    
@ev.stack2args(2)
def LET( state, A, B ):
  symtable = state['symtable'][A] = B
  return [ B ]
  
class PUSH:
  def __init__(self, N ):
    self.value = N
  def __call__( self, state ):
    state['stack'].append( self.value )
  def __repr__(self):
    return '<PUSH '+str(self.value)+'>'