import generator.visitor as vis
from copy import copy, deepcopy
from .Failure import ParserFailedException

class ParseVisitor(vis.Visitor):
  def __init__( self, lexer, terminals, transforms ):
    self.transforms = transforms
    self.terminals = terminals
    self.lexer = lexer
    self.state = [] # ParserState()
  
  def _fork( self ):
    frk = ParseVisitor( self.lexer.fork(), self.terminals, self.transforms )
    frk.state = self.state[:]
    return frk
  
  def _join( self, frk ):
    self.lexer.join( frk.lexer )
    self.state = frk.state
    
  def Parser( visited, self ):
    return visited( self.lexer )
    
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
    return transformed
    
  def Terminal( visited, self ):
    try:
      result = self.lexer.get( visited.terminal )
    except AttributeError:
      try:
        visited.terminal = self.terminals[visited.handle]
        result = self.lexer.get( visited.terminal )
      except KeyError:
        raise RuntimeError('Parser does not handle terminal '+str(visited.handle))
    return [result] if result is not None else None
    
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