from enum import IntEnum, unique
import generator.evaluator as ev

class State:
  __slots__ = '__input', 'stack', 'symtable'
  def __init__(self, input):
    self.input = input
    self.symtable = {}
    self.stack = []  
  
  def save( self ):
    result = State.__new__(State)
    result.input = self.input[:]
    result.stack = self.stack[:]
    result.symtable = dict( self.symtable )
    return result
    
  def load( self, saved ):
    self.__input  = saved.input
    self.stack    = saved.stack
    self.symtable = saved.symtable
    
  @property
  def input( self ):
    return self.__input
    
  @input.setter
  def input( self, value ):
    self.__input = value.lstrip(' ')

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
  symtable = state.symtable[A] = B
  return [ B ]
  
class PUSH:
  def __init__(self, N ):
    self.value = N
  def __call__( self, state ):
    state.stack.append( self.value )
  def __repr__(self):
    return '<PUSH '+str(self.value)+'>'