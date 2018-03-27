from generator.terminal import ParserFailedException

class RuleCompilerBase:
  __slots__ = 'transforms', 'terminals'
  def __init__( self, terminals ):
    self._terminals = terminals
    super().__init__()
  
  def Terminal( self, target ):
    try:
      target.terminal = self._terminals[target.handle]
    except KeyError:
      raise RuntimeError('Parser does not handle terminal '+str(target.handle)) 
    
    def _Terminal( targetSelf, state ):
      result, state.input = targetSelf.terminal( state.input )
      return result
    
    return _Terminal
    
  def Handle( self, target ):
    def _Handle( targetSelf, state ):
      return targetSelf.rule.accept( targetSelf.rule, state )
    return _Handle
    
  def Not( self, target ):
    def _Not( targetSelf, state ):
      try:
        result = targetSelf.rule.accept( targetSelf.rule, state )
      except ParserFailedException:
        return []
      
      raise ParserFailedException()
    return _Not
    
  def Optional( self, target ):  
    def _Optional( targetSelf, state ):
      save = state.fork()
      try:        
        return targetSelf.rule.accept( targetSelf.rule, state )
      except ParserFailedException:
        state.join( save )
        return []
    return _Optional
  
  def Alternative( self, target ):
    def _Alternative( targetSelf, state ):
      for rule in targetSelf.rules:
        fork = state.fork() # entry state
        try:
          return rule.accept( rule, state )  # try visiting
        except ParserFailedException:
          state.join(fork)        
      
      raise ParserFailedException() # all options exhausted with no match
    return _Alternative
    
  def Sequence( self, target ):
    def _Sequence( targetSelf, state ):
      sequence = [  ]
      for rule in targetSelf.rules:
        sequence += rule.accept( rule, state )
         
      return sequence
    return _Sequence
    
  def Repeat( self, target ):
    def _Repeat( targetSelf, state ):
      sequence = []
      save = None
      try:
        while True:
          save = state.fork() #save state from before visitation
          sequence += targetSelf.rule.accept( targetSelf.rule, state )
      except ParserFailedException:
        state.join( save )  # repeat until failure. Discard failed state
        return sequence
    return _Repeat
      
class Reordering( RuleCompilerBase ):
  def __init__( self, terminals ):
    super().__init__( terminals )
    
  def Push( self, target ):
    def _Push( targetSelf, state ):
      result = targetSelf.rule.accept( targetSelf.rule, state )
      state.stack += result
      return []
    return _Push
  
  def Pull( self, target ):
    def _Pull( targetSelf, state ):
      result = targetSelf.rule.accept( targetSelf.rule, state )
      if len(result) > 0:
        raise RuntimeError("Parser returned with fallthrough:" + str(fallthrough) )
      return state.stack
    return _Pull
  
class Ordered( RuleCompilerBase ):
  def __init__( self, terminals ):
    super().__init__( terminals )
    
  def Push( self, target ):
    def _Push( targetSelf, state ):
      return targetSelf.rule.accept( targetSelf.rule, state )
    return _Push
  
  def Pull( self, target ):
    def _Pull( targetSelf, state ):
      return targetSelf.rule.accept( targetSelf.rule, state )
    return _Pull
