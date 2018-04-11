import re
from copy import copy, deepcopy

__all__ = [ 'ParserFailedException', 'Return', 'Switch' ]

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
  def __call__( self, evaluator ):
    result = self.task( evaluator )
    return self.returned

class Return(TerminalBase):
  def __init__( self, *returned ):
    self.returned = list(returned)
  def __call__( self, *args ):
    return self.returned
  
class Wrapper(TerminalBase):
  def __init__( self, wrapped, wrapper ):
    self.wrapped = wrapped
    self.wrapper = wrapper
    
  def __call__( self, evaluator ):
    result = self.wrapped( evaluator )
    return self.wrapper( result )

class Switch(TerminalBase):
  def __init__( self, lookup ):
    self._lookup = [ (re.compile( pattern ),callback) for (pattern, callback ) in lookup.items() ]
    
  def __deepcopy__( self, memo ):
    return copy( self )
    
  def __call__( self, evaluator ):
    for re,callback in self._lookup:
      match = re.match( evaluator.state.input )
      if match is not None:
        evaluator.state.input = match.string[match.end(0):]
        return callback( match )
    
    raise ParserFailedException('Switch exhausted with no matches')