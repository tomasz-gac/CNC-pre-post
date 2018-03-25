from generator.terminal import TerminalBase
from generator.terminal import ParserFailedException

# Injector class injects accept method to a given type
# Accept method implementation is yanked from method with name
# corresponding to injected type name

class Injector:
  def __init__( self ):
    self._visited = set()
  def __call__( self, injected, reinject = False ):
    method_name = 'accept'
    name = type(injected).__name__
    
    if injected in self._visited:
      return injected
    else:
      if (not reinject) and hasattr( injected, method_name ):
        raise RuntimeError("Object " + injected.__repr__() + " has already been injected with method " + method_name )
      if not hasattr( type(self), name ):
        raise RuntimeError("Class " + type(self).__name__ + " does not support visitation of type " + name )
      self._visited.add(injected)
    
    method = getattr( type(self), name )
    setattr( injected, method_name, method )

    for child in injected:
      self( child, reinject )
    return injected
    

class ParseInjector( Injector ):
  __slots__ = 'transforms', 'terminals'
  def __init__( self ):
    super().__init__()
  
  def Terminal( injected, parser ):
    try:
      terminal = injected.terminal      
    except AttributeError:
      try:
        injected.terminal = parser.terminals[injected.handle]
        terminal = injected.terminal
      except KeyError:
        raise RuntimeError('Parser does not handle terminal '+str(injected.handle))
    
    result, rest = terminal( parser.input )
    if rest is not None:
      parser.input = rest
    
    return result
    
  def Handle( injected, parser ):
    return injected.rule.accept( injected.rule, parser )
    
  def Not( injected, parser ):
    try:
      result = injected.rule.accept( injected.rule, parser )
    except ParserFailedException:
      return None
    
    raise ParserFailedException()
    
  def Optional( injected, parser ):
    fork = parser._fork()
    try:
      result = injected.rule.accept( injected.rule, fork )
    except ParserFailedException:
      return None
    
    parser._join( fork )
    return result
    
  def Alternative( injected, parser ):    
    for rule in injected.rules:
      fork = parser._fork() # entry state
      try:
        return rule.accept( rule, parser )  # try visiting
      except ParserFailedException:
        parser._join(fork)        
    
    raise ParserFailedException() # all options exhausted with no match
    
    
  def Sequence( injected, parser ):
    sequence = []
    for rule in injected.rules:
      result = rule.accept( rule, parser )
      if result is not None:
        sequence += result
       
    return sequence
    
  def Repeat( injected, parser ):
    sequence = []
    save = None
    try:
      while True:
        save = parser._fork() #save state from before visitation
        result = injected.rule.accept( injected.rule, parser )
        if result is not None:
          sequence += result 
    except ParserFailedException:
      parser._join( save )  # repeat until failure. Discard failed state
      return sequence
      
class ReorderInjector( ParseInjector ):
  def __init__( self ):
    super().__init__( )
    
  def Push( injected, parser ):
    result = injected.rule.accept( injected.rule, parser )
    if result is not None:
      parser.state += result
    return None
  
  def Pull( injected, parser ):
    result = injected.rule.accept( injected.rule, parser )
    if isinstance( result, list ) and len(result) == 0:
      return parser.state
    if result is not None:
      raise RuntimeError("Parser returned with fallthrough:" + str(fallthrough) )
    return parser.state
  
class InorderInjector( ParseInjector ):
  def __init__( self ):
    super().__init__( )
    
  def Push( injected, parser ):
    return injected.rule.accept( injected.rule, parser )
  
  def Pull( injected, parser ):
    return injected.rule.accept( injected.rule, parser )
