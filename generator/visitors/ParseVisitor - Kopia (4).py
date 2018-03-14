import generator.visitor as vis
from copy import copy

class ParserFailedType:
  pass
  
ParserFailed = ParserFailedType()

class ParseResult:
  def __init__( self, result = None ):
    self.result = result

def _failure( result, success ):
  # return not success or result is ParserFailed
  return result is ParserFailed

class ParseVisitor(vis.Visitor):
  def __init__( self, handlers, defaultHandler ):
    self.handlers = handlers
    self.defaultHandler = defaultHandler
    self.result = []
  
  def _handle( self, rule, result ):
    return self.handlers.get(rule, self.defaultHandler)(result)
  
  def try_visit( self, rule, lexer ):
    fork = lexer.fork()
    result = self.visit( visited.rule, fork )
    if not _failure( result, fork.success ):
      lexer.join(fork)
    return result
    
  def Parser( self, visited, lexer ):
    return visited( lexer )
  
  def Handle( self, visited, lexer ):
    result = self.visit( visited.rule, lexer )
    
    if _failure(result, lexer.success):
      return ParserFailed
    
    return self._handle(visited, result)
    
  def Not( self, visited, lexer ):
    result = self.visit( visited.rule, lexer )
    
    if not _failure(result, lexer.success):
      return ParserFailed
    
    return self._handle( visited, None )
    
  def Optional( self, visited, lexer ):
    result = self._try_visit( visited.rule, lexer )
    if _failure(result, lexer.success ):
      return self._handle( visited, None )
    
    return self._handle( visited, result )
    
  def Alternative( self, visited, lexer ):    
    result = ParserFailed
    for rule in visited.options:
      fork = lexer.fork()
      result = self.visit( rule, fork )
      if not _failure(result, fork.success):
        lexer.join( fork )
        break
    # debug_print( str(self) + " " + str(not _failure(result, lexer.success)) + " / " + lexer._input )
    result = self._handle(visited, result) if result is not ParserFailed else ParserFailed
    return result
    
  def Sequence( self, visited, lexer ):
    sequence = []
    for rule in visited.sequence:
      result = self.visit( rule, lexer )
      if _failure(result, lexer.success): 
        # debug_print( str(self) + " " + str(not _failure(result, lexer.success)) + " / " + lexer._input )
        return ParserFailed
      if result is not None:
        sequence += result
    
    # debug_print( str(self) + " " + str(True) + " / " + lexer._input )
    return self._handle(visited, sequence)
    
  def Repeat( self, visited, lexer ):
    fork = lexer.fork()
    sequence = []
    while True:
      result = self.visit( visited.rule, fork )
      if _failure(result, fork.success):
        lexer.join( fork )
        # debug_print( str(self) + " " + str(True) + " / " + lexer._input )
        return self._handle(visited, sequence)
      if result is not None:
        sequence += result 
      
  def Terminal( self, visited, lexer):
    #get a token from lexer, see if lexing failed
    token = lexer.get( visited.task )
    token = ParserFailed if token is None else token
      #return if error or EOL
    if _failure(token, lexer.success):
      # debug_print( str(self) + " " + str(not _failure(token, lexer.success)) + " / " + lexer._input )
      return ParserFailed
      # handle the token and return the result
    # debug_print( str(self) + " " + str(True) + " / " + lexer._input )
    return [ self._handle(visited, token) ]
  
  def TerminalString( self, visited, lexer ):
    return self.Terminal( visited, lexer )
    
  def Always( self, visited, lexer ):
    return self._handle( visited, None)
  
  def Never( self, visited, lexer ):
    return ParserFailed
    
  def Ignore( self, visited, lexer ):
    result = self.visit( visited.rule, lexer )
    if _failure( result, lexer.success ):
      return ParserFailed
    else:      
      return self._handle( visited, None )
  
  def Bracket( self, visited, lexer ):
    result = self.visit( visited.rule, lexer )
    if not _failure( result, lexer.success ):
      if result is not None: 
        self.result.append( ( id(visited.rule), self._handle( visited, result ) ) )
        # return self._handle( visited, result ), success
      return None
    else:
      return ParserFailed