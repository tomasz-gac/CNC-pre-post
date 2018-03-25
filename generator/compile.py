from generator.terminal import TerminalBase
from generator.terminal import ParserFailedException
from copy import deepcopy

# Injector class injects accept method to a given type
# Accept method implementation is yanked from method with name
# corresponding to target type name

class Injector:
  def __init__( self, injection ):
    self._visited   = set()
    self.injection  = injection
    
  def __call__( self, target, reinject = False ):
    method_name = 'accept'
    name = type(target).__name__
    
    if target in self._visited:
      return target
    else:
      if (not reinject) and hasattr( target, method_name ):
        raise RuntimeError("Object " + target.__repr__() + " has already injected with method " + method_name )
      if not hasattr( self.injection, name ):
        raise RuntimeError("Class " + type(self.injection).__name__ + " does not support injection for type " + name )
      self._visited.add(target)
    
    method = getattr( self.injection, name )
    setattr( target, method_name, method(target) )

    for child in target:
      self( child, reinject )
    return target
    
def compile( rule, compiler ):
  return Injector( compiler )( deepcopy( rule ) )

class RuleCompilerBase:
  __slots__ = 'transforms', 'terminals'
  def __init__( self, terminals ):
    self._terminals = terminals
    super().__init__()
  
  def Terminal( self, target ):
    try:
      target.terminal = self._terminals[target.handle]
    except KeyError:
      raise RuntimeError('Parser does not handle terminal '+str(target.handle)) 
    
    def accept( targetSelf, parser ):
      result, parser.input = targetSelf.terminal( parser.input )
      return result
    
    return accept
    
  def Handle( self, target ):
    def accept( targetSelf, parser ):
      return targetSelf.rule.accept( targetSelf.rule, parser )
    return accept
    
  def Not( self, target ):
    def accept( targetSelf, parser ):
      try:
        result = targetSelf.rule.accept( targetSelf.rule, parser )
      except ParserFailedException:
        return None
      
      raise ParserFailedException()
    return accept
    
  def Optional( self, target ):  
    def accept( targetSelf, parser ):
      fork = parser._fork()
      try:
        result = targetSelf.rule.accept( targetSelf.rule, fork )
      except ParserFailedException:
        return None
      
      parser._join( fork )
      return result
    return accept
  
  def Alternative( self, target ):
    def accept( targetSelf, parser ):
      for rule in targetSelf.rules:
        fork = parser._fork() # entry state
        try:
          return rule.accept( rule, parser )  # try visiting
        except ParserFailedException:
          parser._join(fork)        
      
      raise ParserFailedException() # all options exhausted with no match
    return accept
    
  def Sequence( self, target ):
    def accept( targetSelf, parser ):
      sequence = []
      for rule in targetSelf.rules:
        result = rule.accept( rule, parser )
        if result is not None:
          sequence += result
         
      return sequence
    return accept
    
  def Repeat( self, target ):
    def accept( targetSelf, parser ):
      sequence = []
      save = None
      try:
        while True:
          save = parser._fork() #save state from before visitation
          result = targetSelf.rule.accept( targetSelf.rule, parser )
          if result is not None:
            sequence += result 
      except ParserFailedException:
        parser._join( save )  # repeat until failure. Discard failed state
        return sequence
    return accept
      
class Reordering( RuleCompilerBase ):
  def __init__( self, terminals ):
    super().__init__( terminals )
    
  def Push( self, target ):
    def accept( targetSelf, parser ):
      result = targetSelf.rule.accept( targetSelf.rule, parser )
      if result is not None:
        parser.state += result
      return None
    return accept
  
  def Pull( self, target ):
    def accept( targetSelf, parser ):
      result = targetSelf.rule.accept( targetSelf.rule, parser )
      if isinstance( result, list ) and len(result) == 0:
        return parser.state
      if result is not None:
        raise RuntimeError("Parser returned with fallthrough:" + str(fallthrough) )
      return parser.state
    return accept
  
class Ordered( RuleCompilerBase ):
  def __init__( self, terminals ):
    super().__init__( terminals )
    
  def Push( self, target ):
    def accept( targetSelf, parser ):
      return targetSelf.rule.accept( targetSelf.rule, parser )
    return accept
  
  def Pull( self, target ):
    def accept( targetSelf, parser ):
      return targetSelf.rule.accept( targetSelf.rule, parser )
    return accept
