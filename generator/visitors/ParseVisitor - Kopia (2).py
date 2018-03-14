import generator.visitor as vis

class ParserFailedType:
  pass
  
ParserFailed = ParserFailedType()

def _failure( result, success ):
  return not success or result is ParserFailed
  
class ParseVisitor(vis.Visitor):
  def __init__( self, handlers, defaultHandler ):
    self.handlers = handlers
    self.defaultHandler = defaultHandler
  
  def _handle( self, rule, result ):
    return self.handlers.get(rule, self.defaultHandler)(result)
    
  def Parser( self, visited, lexer ):
    return visited( lexer )
  
  def Handle( self, visited, lexer ):
    result, success = self.visit( visited.rule, lexer )
    
    if _failure(result, success):
      return ParserFailed, success
    
    return self._handle(visited, result), success 
    
  def Not( self, visited, lexer ):
    result, success = self.visit( visited.rule, lexer )
    
    if not _failure(result, success):
      return ParserFailed, False
    
    return self._handle( visited, None ), True
    
  def Optional( self, visited, lexer ):
    fork = lexer.fork()
    # out = output[:]
    result, success = self.visit( visited.rule, fork )
    if _failure(result, success):
      return self._handle( visited, None ), True
    
    lexer.join( fork )
    #output[:] = out[:]
    return self._handle( visited, result ), success 
    
  def Alternative( self, visited, lexer ):    
    result, success = ParserFailed, False
    # out = []
    for rule in visited.options:
      fork = lexer.fork()
      # out = output[:]
      result, s = self.visit( rule, fork )
      success = s or success
      if not _failure(result, s):
        lexer.join( fork )
        # output[:] = out[:]
        break
    # debug_print( str(self) + " " + str(not _failure(result, success)) + " / " + lexer._input )
    result = self._handle(visited, result) if result is not ParserFailed else ParserFailed
    return result, success
    
  def Sequence( self, visited, lexer ):
    sequence = []
    for rule in visited.sequence:
      result, success = self.visit( rule, lexer )
      if _failure(result, success): 
        # debug_print( str(self) + " " + str(not _failure(result, success)) + " / " + lexer._input )
        return ParserFailed, success
      if result is not None:
        sequence += result
      # sequence.append(result)
    
    # debug_print( str(self) + " " + str(True) + " / " + lexer._input )
    return self._handle(visited, sequence), True
    
  def Repeat( self, visited, lexer ):
    fork = lexer.fork()
    # out = output[:]
    sequence = []
    while True:
      result, success = self.visit( visited.rule, fork )
      if _failure(result, success):
        lexer.join( fork )
        # output[:] = out[:]
        # debug_print( str(self) + " " + str(True) + " / " + lexer._input )
        return self._handle(visited, sequence), True
      if result is not None:
        sequence += result
      # sequence.append(result)      
      
  def Terminal( self, visited, lexer):
    #get a token from lexer, see if lexing failed
    token, success = lexer.get( visited.task )
    token = ParserFailed if token is None else token
      #return if error or EOL
    if _failure(token, success):
      # debug_print( str(self) + " " + str(not _failure(token, success)) + " / " + lexer._input )
      return ParserFailed, success
      # handle the token and return the result
    # debug_print( str(self) + " " + str(True) + " / " + lexer._input )
    return [ self._handle(visited, token) ], True
  
  def TerminalString( self, visited, lexer ):
    return self.Terminal( visited, lexer )
    
  def Always( self, visited, lexer ):
    return self._handle( visited, None), True
  
  def Never( self, visited, lexer ):
    return ParserFailed, False
    
  def Ignore( self, visited, lexer ):
    result, success = self.visit( visited.rule, lexer )
    if not _failure( result, success ):
      return self._handle( visited, None), True
    else:
      return ParserFailed, False
  
  def Bracket( self, visited, lexer ):
    result, success = self.visit( visited.rule, lexer )
    if not _failure( result, success ):
      if result is not None:
        yield self._handle( visited, result ), success
      return None, True
    else:
      return ParserFailed, False