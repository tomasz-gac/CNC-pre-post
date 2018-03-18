import generator.visitor as vis
from copy import copy
from .Failure import ParserFailed

class ParseVisitor(vis.Visitor):
  def __init__( self, lexer, handlers, defaultHandler ):
    self.handlers = handlers
    self.defaultHandler = defaultHandler
    self.table = {}
    self.lexer = lexer
    self.result = []
  
  def _handle( self, rule, result ):
    return self.handlers.get(rule, self.defaultHandler)(result)
    
    
  def _fork( self ):
    frk = ParseVisitor( self.lexer.fork(), self.handlers, self.defaultHandler )
    frk.result = self.result[:]
    frk.table = copy(self.table)
    return frk
  
  def _join( self, frk ):
    self.lexer.join( frk.lexer )
    self.result = frk.result
    frk.result = []
    self.table = frk.table
    frk.table = {}
    
  def Parser( self, visited ):
    return self._handle( visited, visited( self.lexer ) )
    
  def Push( self, visited ):
    result = self.visit( visited.rule )
    if ParserFailed( result, self.lexer.success ):
      return ParserFailed
    elif result is not None:
      self.result += self._handle( visited, result )
    return None  

  def Handle( self, visited ):
    result = self.visit( visited.rule )
    
    if ParserFailed(result, self.lexer.success):
      return ParserFailed
    
    return self._handle(visited, result)
    
  def Not( self, visited ):
    result = self.visit( visited.rule )
    
    if not ParserFailed(result, self.lexer.success):
      return ParserFailed
    
    return self._handle( visited, None )
    
  def Optional( self, visited ):
    fork = self._fork()
    result = fork.visit( visited.rule )
    if ParserFailed(result, fork.lexer.success ):
      return self._handle( visited, None )
    
    self._join( fork )
    return self._handle( visited, result )
    
  def Alternative( self, visited ):    
    result = ParserFailed
    for rule in visited.options:
      fork = self._fork()
      result = fork.visit( rule )
      if not ParserFailed(result, fork.lexer.success):
        self._join( fork )
        break
    result = self._handle(visited, result) if result is not ParserFailed else ParserFailed
    return result
    
  def Sequence( self, visited ):
    sequence = []
    for rule in visited.sequence:
      result = self.visit( rule )
      if ParserFailed(result, self.lexer.success): 
        return ParserFailed
      if result is not None:
        sequence += result
    
    return self._handle(visited, sequence)
    
  def Repeat( self, visited ):
    sequence = []
    while True:
        #if visitation fails - return to state from before visitation
      tmp = self._fork()
      result = self.visit( visited.rule )
      if ParserFailed(result, self.lexer.success):
        self._join( tmp )
        return self._handle(visited, sequence)
      if result is not None:
        sequence += result 
      
  def Terminal( self, visited):
    #get a result from lexer, see if lexing failed
    result = self.lexer.get( visited.task )
    result = ParserFailed if result is None else result
      #return if error or EOL
    if ParserFailed(result, self.lexer.success):
      return ParserFailed
      # handle the result and return the result
    result = self._handle(visited, result)
    return result if isinstance( result, list ) else [result]
  
  def TerminalString( self, visited ):
    return self.Terminal( visited )
    
  def Always( self, visited ):
    return self._handle( visited, None)
  
  def Never( self, visited ):
    return ParserFailed
    
  def Ignore( self, visited ):
    result = self.visit( visited.rule )
    if ParserFailed( result, self.lexer.success ):
      return ParserFailed
    else:      
      return self._handle( visited, None )
        
  def Copy( self, visited ):
    result = self.visit( visited.rule )
    if result is not ParserFailed:
      self.table[visited.name] = result
    return result
    
  def Cut( self, visited ):
    result = self.visit( visited.rule )
    if result is not ParserFailed:
      self.table[visited.name] = result
    return self._handle( visited, None )
    
  def Paste( self, visited ):
    if visited.name in self.table:
      return self.table[ visited.name ]
    return ParserFailed
