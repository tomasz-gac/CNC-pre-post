__all__ = [ 'State' ]

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

'''def do_copy( value ):
  if type( value ) is dict:
    raise RuntimeError('Dicts not supported by do_copy. Use State instead.')
  if isinstance( value, ( int, complex, float, bool ) ):
    return value
  if isinstance( value, (list, tuple) ):
    return value[:]
  try:
    return value.__copy__()
  except AtributeError:
    pass
  try:
    return value.copy()
  except AtributeError:
    pass
  raise RuntimeError('Non-copyable object passed to do_copy')
  
    
class State(dict):
  def __copy__( self ):
    return State( { key : do_copy(value) for key,value in self.items() } )
    
  def __repr__( self ):
    return 'State(' + dict.__repr__(self) + ')'
    
  save = __copy__
  load = dict.update
  
def make_state():
  return State( input = '', symtable = State(), stack = [] )'''