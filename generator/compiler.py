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
        return None
      
      raise ParserFailedException()
    return _Not
    
  def Optional( self, target ):  
    def _Optional( targetSelf, state ):
      fork = state._fork()
      try:
        result = targetSelf.rule.accept( targetSelf.rule, fork )
      except ParserFailedException:
        return None
      
      state._join( fork )
      return result
    return _Optional
  
  def Alternative( self, target ):
    def _Alternative( targetSelf, state ):
      for rule in targetSelf.rules:
        fork = state._fork() # entry state
        try:
          return rule.accept( rule, state )  # try visiting
        except ParserFailedException:
          state._join(fork)        
      
      raise ParserFailedException() # all options exhausted with no match
    return _Alternative
    
  def Sequence( self, target ):
    def _Sequence( targetSelf, state ):
      sequence = []
      for rule in targetSelf.rules:
        result = rule.accept( rule, state )
        if result is not None:
          sequence += result
         
      return sequence
    return _Sequence
    
  def Repeat( self, target ):
    def _Repeat( targetSelf, state ):
      sequence = []
      save = None
      try:
        while True:
          save = state._fork() #save state from before visitation
          result = targetSelf.rule.accept( targetSelf.rule, state )
          if result is not None:
            sequence += result 
      except ParserFailedException:
        state._join( save )  # repeat until failure. Discard failed state
        return sequence
    return _Repeat
      
class Reordering( RuleCompilerBase ):
  def __init__( self, terminals ):
    super().__init__( terminals )
    
  def Push( self, target ):
    def _Push( targetSelf, state ):
      result = targetSelf.rule.accept( targetSelf.rule, state )
      if result is not None:
        state.stack += result
      return None
    return _Push
  
  def Pull( self, target ):
    def _Pull( targetSelf, state ):
      result = targetSelf.rule.accept( targetSelf.rule, state )
      if isinstance( result, list ) and len(result) == 0:
        return state.stack
      if result is not None:
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
