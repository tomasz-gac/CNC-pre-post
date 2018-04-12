import re
from copy import copy, deepcopy

__all__ = [ 'ParserFailedException', 'Return', 'Switch', 'If' ]

class ParserFailedException(Exception):
  pass

class TerminalBase:
  def ignore( self, returned = [] ):
    return Ignore( self, returned )
    
  def __rshift__( self, wrapper ):
    return Wrapper( self, wrapper )
  
class Ignore(TerminalBase):
  def __init__( self, task, returned = [] ):
    self.task = make(task)
    self.returned = returned
  def __call__( self, state ):
    result = self.task( state )
    return self.returned

class Return(TerminalBase):
  def __init__( self, *returned ):
    self.returned = returned
  def __call__( self, *args ):
    return self.returned
  
class Wrapper(TerminalBase):
  def __init__( self, wrapped, wrapper ):
    self.wrapped = wrapped
    self.wrapper = wrapper
    
  def __call__( self, state ):
    result = self.wrapped( state )
    return self.wrapper( result )

class Lookup(TerminalBase):
  def __init__( self, lookup ):
    self._lookup = tuple( (re.compile( pattern ), returned) for (pattern, returned) in lookup.items() )
    
  def __deepcopy__( self, memo ):
    return copy( self )
    
  def __call__( self, state ):
    for re, returned in self._lookup:
      match = re.match( state.input )
      if match is not None:
        state.input = match.string[match.end(0):]
        return returned
    
    raise ParserFailedException('Lookup exhausted with no matches')
    
class Switch(TerminalBase):
  def __init__( self, lookup ):
    self._lookup = tuple( (re.compile( pattern ),callback) for (pattern, callback ) in lookup.items() )
    
  def __deepcopy__( self, memo ):
    return copy( self )
    
  def __call__( self, state ):
    for re,callback in self._lookup:
      match = re.match( state.input )
      if match is not None:
        state.input = match.string[match.end(0):]
        return callback( match )
    
    raise ParserFailedException('Switch exhausted with no matches')
    
class If(TerminalBase):
  def __init__( self, pattern, block ):
    self.condition = re.compile( pattern )
    self.block = block
    
  def __deepcopy__( self, memo ):
    return copy( self )
    
  def __call__( self, state ):
    match = self.condition.match( state.input )
    if match is not None:
      state.input = match.string[match.end(0):]
      return self.block( match )
    
    raise ParserFailedException('If terminal did not match')