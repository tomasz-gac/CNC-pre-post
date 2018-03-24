import generator.visitor as vis
from copy import copy, deepcopy
from .Failure import ParserFailedException

# This visitor has reversed order of parameters in handling functions
# because we directly call the bounce-back method of Visitable
# This way we avoid call to Visitor's visit method and gain performance

class ParseVisitor(vis.Visitor):
  __slots__ = 'transforms', 'terminals', 'state', '__input', 'preprocess'
  def __init__( self, terminals, transforms, preprocess ):
    self.transforms = transforms
    self.terminals = terminals
    self.state = []     
    self.__input = None
    self.preprocess = preprocess
  
  def _fork( self ):
    frk = ParseVisitor( self.terminals, self.transforms, self.preprocess )
    frk.state = self.state[:]
    frk.__input = self.__input[:]
    return frk
  
  def _join( self, frk ):
    # self.lexer.join( frk.lexer )
    self.state = frk.state
    self.__input = frk.__input
    
  @property
  def input( self ):
    return self.__input
    
  @input.setter
  def input( self, line ):
    self.__input = self.preprocess( line )
    
  def Transform( visited, self ):
    result = visited.rule.ParseVisitor( self )
    try:
      transformed = visited.transform( result, self.state )
    except AttributeError:
      try:
        visited.transform = self.transforms[visited.handle]
        transformed = visited.transform( result, self.state)      
      except KeyError:
        raise RuntimeError('Parser does not handle transform '+str(visited.handle))
    return transformed #, self.state
    
  def Terminal( visited, self ):
    # terminal = self.terminals[visited.handle] # None
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
    
    return result#  if result is not None else None
    
  def Handle( visited, self ):
    return visited.rule.ParseVisitor( self )
    
  def Not( visited, self ):
    try:
      result = visited.rule.ParseVisitor( self )
    except ParserFailedException:
      return None
    
    raise ParserFailedException()
    
  def Optional( visited, self ):
    fork = self._fork()
    try:
      result = visited.rule.ParseVisitor( fork )
    except ParserFailedException:
      return None
    
    self._join( fork )
    return result
    
  def Alternative( visited, self ):    
    for rule in visited.options:
      fork = self._fork() # entry state
      try:
        return rule.ParseVisitor( self )  # try visiting
      except ParserFailedException:
        self._join(fork)        
    
    raise ParserFailedException() # all options exhausted with no match
    
    
  def Sequence( visited, self ):
    sequence = []
    for rule in visited.sequence:
      result = rule.ParseVisitor( self )
      if result is not None:
        sequence += result
       
    return sequence
    
  def Repeat( visited, self ):
    sequence = []
    save = None
    try:
      while True:
        save = self._fork() #save state from before visitation
        result = visited.rule.ParseVisitor( self )
        if result is not None:
          sequence += result 
    except ParserFailedException:
      self._join( save )  # repeat until failure. Discard failed state
      return sequence      