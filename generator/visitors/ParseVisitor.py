import generator.visitor as vis
from copy import copy, deepcopy
from .Failure import ParserFailedException

class ParseVisitor(vis.Visitor):
  def __init__( self, lexer, transforms ):
    self.transforms = transforms
    self.lexer = lexer
    self.state = [] # ParserState()
  
  def _fork( self ):
    frk = ParseVisitor( self.lexer.fork(), self.transforms )
    frk.state = self.state[:]
    return frk
  
  def _join( self, frk ):
    self.lexer.join( frk.lexer )
    self.state = frk.state
    frk.state = []
    
  def Parser( self, visited ):
    return visited( self.lexer )
    
  def Transform( self, visited ):
    result = self.visit( visited.rule )
    # if ParserFailed(result, self.lexer.success):
      # return ParserFailed
      # Expects all transforms to be handled
    return self.transforms[visited.handle]( result, self.state)
    
  def Handle( self, visited ):
    result = self.visit( visited.rule )
    
    # if ParserFailed(result, self.lexer.success):
      # return ParserFailed
    
    return result
    
  def Not( self, visited ):
    try:
      result = self.visit( visited.rule )
    except ParserFailedException:
      return None
    
    raise ParserFailedException()
    
  def Optional( self, visited ):
    fork = self._fork()
    try:
      result = fork.visit( visited.rule )
    except ParserFailedException:
      return None
    
    self._join( fork )
    return result
    
  def Alternative( self, visited ):    
    for rule in visited.options:
      fork = self._fork()
      try:
        result = fork.visit( rule )
        self._join( fork )
        return result
      except ParserFailedException:
        pass      
    
    raise ParserFailedException()
    
    
  def Sequence( self, visited ):
    sequence = []
    for rule in visited.sequence:
      result = self.visit( rule )
      if result is not None:
        sequence += result
    
    return sequence
    
  def Repeat( self, visited ):
    sequence = []
    while True:
        #if visitation fails - return to state from before visitation
      tmp = self._fork()
      try:
        result = self.visit( visited.rule )
        if result is not None:
          sequence += result 
      except ParserFailedException:
        self._join( tmp )
        return sequence      
      
  def Terminal( self, visited):
    #get a result from lexer, see if lexing failed
    result = self.lexer.get( visited.task )
      #return if error or EOL
    if result is None:
      raise ParserFailedException()
    
    return [result]
  
  def TerminalString( self, visited ):
    return self.Terminal( visited )
  
  def Ignore( self, visited ):
    result = self.visit( visited.rule )
    return None
   
  '''def Always( self, visited ):
    return None
  
  def Never( self, visited ):
    return ParserFailed
    
        
  def Copy( self, visited ):
    result = self.visit( visited.rule )
    if result is not ParserFailed:
      self.table[visited.name] = result
    return result
    
  def Cut( self, visited ):
    result = self.visit( visited.rule )
    if result is not ParserFailed:
      self.table[visited.name] = result
    return None
    
  def Paste( self, visited ):
    if visited.name in self.table:
      return self.table[ visited.name ]
    return ParserFailed'''
