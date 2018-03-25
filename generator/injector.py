from generator.terminal import TerminalBase
from generator.terminal import ParserFailedException
from generator.RecursionGuard import RecursionGuard      

# Injector class injects accept method to a given type
# Accept method implementation is yanked from method with name
# corresponding to injected type name

class Injector:
  def __init__( self ):
    self.visited = RecursionGuard()
  def __call__( self, injected ):
    if self.visited( injected ):
      return
    
    name = type(injected).__name__
    myname = type(self).__name__    
    if not hasattr( type(injected), 'accept' ):
      if hasattr( type(self), name ):
        method = getattr( type(self), name )
        setattr( injected, 'accept', method )
      else:
        raise RuntimeError("Class " + myname + " does not support visitation of type " + name )
    for child in injected:
      self( child )
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
  
  '''def Transform( injected, parser ):
    result = injected.rule.ParseInjector( parser )
    try:
      transformed = injected.transform( result, parser )
    except AttributeError:
      try:
        injected.transform = parser.injector.transforms[injected.handle]
        transformed = injected.transform( result, parser )      
      except KeyError:
        raise RuntimeError('Parser does not handle transform '+str(injected.handle))
    return transformed'''
    
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
