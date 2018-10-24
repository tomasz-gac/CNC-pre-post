from copy import copy, deepcopy

__all__ = [ 'ParserFailedException', 'Wrapper', 'Return', 'Switch', 'Lookup', 'If', 'Push', 'pushTerminals' ]

class ParserFailedException(Exception):
  pass

class TerminalBase:
  def If( self, condition ):
    return If( condition, self )
    
  def __rshift__( self, wrapper ):
    return Wrapper( self, wrapper )
  
class Ignore(TerminalBase):
  def __init__( self, ignored, returned = () ):
    self.ignored = ignored
    self.returned = returned
  def __call__( self, state ):
    self.ignored( state )
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
    self._lookup = lookup
    
  def __deepcopy__( self, memo ):
    return copy( self )
    
  def __call__( self, state ):
    for condition, returned in self._lookup:
      match = condition.match( state.input )
      if match is not None:
        state.input = match.string[match.end(0):]
        return returned
    
    raise ParserFailedException('Lookup exhausted with no matches')
    
class Switch(TerminalBase):
  def __init__( self, lookup ):
    self._lookup = lookup
    
  def __deepcopy__( self, memo ):
    return copy( self )
    
  def __call__( self, state ):
    for condition,callback in self._lookup:
      match = condition.match( state.input )
      if match is not None:
        state.input = match.string[match.end(0):]
        return callback( match )
    
    raise ParserFailedException('Switch exhausted with no matches')
    
class If(TerminalBase):
  def __init__( self, condition, block ):
    self.condition = condition
    self.block = block
    
  def __deepcopy__( self, memo ):
    return copy( self )
    
  def __call__( self, state ):
    match = self.condition.match( state.input )
    if match is not None:
      state.input = match.string[match.end(0):]
      return self.block( match )
    
    raise ParserFailedException('If terminal did not match')
    
class Push:
  def __init__(self, N ):
    self.value = N
  def __call__( self, state ):
    state.stack.append( self.value )
  def __repr__(self):
    return '<PUSH '+str(self.value)+'>'

def push( value ):
  def _push( state ):
    state.stack.append( value )
  return (_push,)
    
def pushTerminals( terminals ):
  return { key : Wrapper( value, push ) for (key, value) in terminals.items() }