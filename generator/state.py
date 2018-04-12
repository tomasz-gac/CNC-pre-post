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
