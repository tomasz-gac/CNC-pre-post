import generator.visitor as vis
from copy import copy, deepcopy
from .Failure import ParserFailedException
from generator.terminal import TerminalBase

# This visitor has reversed order of parameters in handling functions
# because we directly call the bounce-back method of Visitable
# This way we avoid call to Visitor's visit method and gain performance

class Parser(TerminalBase):
  __slots__ = 'rule', 'transforms', 'terminals', 'state', '__input', 'preprocess'
  def __init__( self, rule, terminals, transforms, preprocess = lambda s : s.lstrip(' ')  ):
    self.rule = rule
    self.transforms = transforms
    self.terminals  = terminals
    self.preprocess = preprocess
    
    self.state = []
    self.__input = None
    
    super().__init__()
  
  def __call__( self, input ):
    self.input = input
    self.state = []
    result = self.rule.Parser( self )
    return result, self.input
  
  def _fork( self ):
    frk = Parser( self.rule, self.terminals, self.transforms, self.preprocess )
    frk.state = self.state[:]
    frk.__input = self.__input[:]
    return frk
  
  def _join( self, frk ):
    self.state = frk.state
    self.__input = frk.__input
    
  @property
  def input( self ):
    return self.__input
    
  @input.setter
  def input( self, line ):
    self.__input = self.preprocess( line )
    
  def Terminal( visited, self ):
    try:
      terminal = visited.terminal      
    except AttributeError:
      try:
        visited.terminal = self.terminals[visited.handle]
        terminal = visited.terminal
      except KeyError:
        raise RuntimeError('Parser does not handle terminal '+str(visited.handle))
    
    result, rest = terminal( self.input )
    if rest is not None:
      self.input = rest
    
    return result
  
  def Transform( visited, self ):
    result = visited.rule.Parser( self )
    try:
      transformed = visited.transform( result, self )
    except AttributeError:
      try:
        visited.transform = self.transforms[visited.handle]
        transformed = visited.transform( result, self )      
      except KeyError:
        raise RuntimeError('Parser does not handle transform '+str(visited.handle))
    return transformed
    
  def Handle( visited, self ):
    return visited.rule.Parser( self )
    
  def Not( visited, self ):
    try:
      result = visited.rule.Parser( self )
    except ParserFailedException:
      return None
    
    raise ParserFailedException()
    
  def Optional( visited, self ):
    fork = self._fork()
    try:
      result = visited.rule.Parser( fork )
    except ParserFailedException:
      return None
    
    self._join( fork )
    return result
    
  def Alternative( visited, self ):    
    for rule in visited.options:
      fork = self._fork() # entry state
      try:
        return rule.Parser( self )  # try visiting
      except ParserFailedException:
        self._join(fork)        
    
    raise ParserFailedException() # all options exhausted with no match
    
    
  def Sequence( visited, self ):
    sequence = []
    for rule in visited.sequence:
      result = rule.Parser( self )
      if result is not None:
        sequence += result
       
    return sequence
    
  def Repeat( visited, self ):
    sequence = []
    save = None
    try:
      while True:
        save = self._fork() #save state from before visitation
        result = visited.rule.Parser( self )
        if result is not None:
          sequence += result 
    except ParserFailedException:
      self._join( save )  # repeat until failure. Discard failed state
      return sequence      