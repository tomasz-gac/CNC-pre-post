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
    
  def Parser( visited, self ):
    return visited( self.lexer )
    
  def Transform( visited, self ):
    result = visited.rule.ParseVisitor( self )
    # if ParserFailed(result, self.lexer.success):
      # return ParserFailed
      # Expects all transforms to be handled
    return self.transforms[visited.handle]( result, self.state)
    
  def Handle( visited, self ):
    result = visited.rule.ParseVisitor( self )
    
    # if ParserFailed(result, self.lexer.success):
      # return ParserFailed
    
    return result
    
  def Not( visited, self ):
    try:
      result = visited.rule.ParseVisitor( self )
    except ParserFailedException:
      return None
    
    raise ParserFailedException()
    
  def Optional( visited, self ):
    fork = self._fork()
    try:
      result = visited.rule.ParserVisitor( fork )
    except ParserFailedException:
      return None
    
    self._join( fork )
    return result
    
  def Alternative( visited, self ):    
    for rule in visited.options:
      try:
        fork = self._fork()
        result = rule.ParseVisitor( fork )
        self._join( fork )
        return result
      except ParserFailedException:
        pass      
    
    raise ParserFailedException()
    
    
  def Sequence( visited, self ):
    '''sequence = [ 
      result for result in ( 
        rule.ParseVisitor( self ) for rule in visited.sequence 
        ) if result is not None 
      ]'''
    sequence = []
    for rule in visited.sequence:
      result = rule.ParseVisitor( self )
      if result is not None:
        sequence += result
       
    return sequence
    
  def Repeat( visited, self ):
    sequence = []
    tmp = None
    try:
      while True:
          #if visitation fails - return to state from before visitation
        tmp = self._fork()
        result = visited.rule.ParseVisitor( self )
        if result is not None:
          sequence += result 
    except ParserFailedException:
      self._join( tmp )
      return sequence      
      
  def Terminal( visited, self ):
    #get a result from lexer, see if lexing failed
    result = self.lexer.get( visited.task )
      #return if error or EOL
    if result is None:
      raise ParserFailedException()
    
    return [result]
  
  def TerminalString( visited, self ):
    return ParseVisitor.Terminal( visited, self )
  
  def Ignore( visited, self ):
    result = visited.rule.ParseVisitor( self )
    return None