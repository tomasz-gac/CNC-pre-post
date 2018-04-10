import re
from copy import copy, deepcopy
from generator.injector import Injector
from generator.evaluator import Eager, Delayed

__all__ = [ 'ParserFailedException', 'Parser', 'Return', 'Switch' ]

class TerminalBase:
  def ignore( self, returned = [] ):
    return Ignore( self, returned )
    
  def __rshift__( self, wrapper ):
    return Wrapper( self, wrapper )
    return Wrapper( self, wrapper )
    
class ParserFailedException( Exception ):
  def __init__( self, string ):
    super().__init__(string)

class Parser(TerminalBase):
  __slots__ = 'rule', 'Evaluator'
  def __init__( self, rule, Evaluator, compiler, recompile = False ):
    self.rule = Injector(compiler)( deepcopy( rule ), recompile )
    self.Evaluator = Evaluator
  
  def __call__( self, state ):
    evaluator = self.Evaluator(state)
    evaluator.state.load( evaluator.state.save() )  # do not modify the incoming state
    result = self.rule.accept( self.rule, evaluator )
    if len(result) > 0:
      raise RuntimeError('Parser returned with fallthrough: ' + str(result) )
    return evaluator.state
  
class Ignore(TerminalBase):
  def __init__( self, task, returned = [] ):
    self.task = make(task)
    self.returned = returned
  def __call__( self, state ):
    result = self.task(state)
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
    
  def __call__( self, state ):
    result = self.wrapped( state )
    return self.wrapper( result )

class Switch(TerminalBase):
  def __init__( self, lookup ):
    self._lookup = { re.compile( pattern ) : callback for (pattern, callback ) in lookup.items() }
    
  def __deepcopy__( self, memo ):
    return copy( self )
    
  def __call__( self, state ):
    for re,callback in self._lookup.items():
      match = re.match( state.input )
      if match is not None:
        state.input = match.string[match.end(0):]
        return callback( match )
    
    raise ParserFailedException('Pattern exhausted with no matches')