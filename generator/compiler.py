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
    
    def _Terminal( targetSelf, executor ):
      result, executor.input = targetSelf.terminal( executor.input )
      return result
    
    return _Terminal
    
  def Handle( self, target ):
    def _Handle( targetSelf, executor ):
      return targetSelf.rule.accept( targetSelf.rule, executor )
    return _Handle
    
  def Not( self, target ):
    def _Not( targetSelf, executor ):
      try:
        result = targetSelf.rule.accept( targetSelf.rule, executor )
      except ParserFailedException:
        return []
      
      raise ParserFailedException('Parser marched a Not statement')
    return _Not
    
  def Optional( self, target ):  
    def _Optional( targetSelf, executor ):
      save = executor.fork()
      try:        
        return targetSelf.rule.accept( targetSelf.rule, executor )
      except ParserFailedException:
        executor.join( save )
        return []
    return _Optional
  
  def Alternative( self, target ):
    def _Alternative( targetSelf, executor ):
      for rule in targetSelf.rules:
        fork = executor.fork() # entry executor
        try:
          return rule.accept( rule, executor )  # try visiting
        except ParserFailedException:
          executor.join(fork)        
      
      raise ParserFailedException('Parser alternative exhausted with no match') # all options exhausted with no match
    return _Alternative
    
  def Sequence( self, target ):
    def _Sequence( targetSelf, executor ):
      sequence = [  ]
      for rule in targetSelf.rules:
          # Execute eagerly
        result = rule.accept( rule, executor )
        sequence += executor( result )
         
      return sequence
    return _Sequence
    
  def Repeat( self, target ):
    def _Repeat( targetSelf, executor ):
      sequence = []
      save = None
      try:
        while True:
          save = executor.fork() #save executor from before visitation
          sequence += targetSelf.rule.accept( targetSelf.rule, executor )
      except ParserFailedException:
        executor.join( save )  # repeat until failure. Discard failed executor
        return sequence
    return _Repeat
    
  def Push( self, target ):
      # Do not execute
    def _Push( targetSelf, executor ):
      result = targetSelf.rule.accept( targetSelf.rule, executor )
      return result
    return _Push
      
class Reordering( RuleCompilerBase ):
  def __init__( self, terminals ):
    super().__init__( terminals )
    
  def Sequence( self, target ):
      # Start executing after obtaining all of sequence
    def _Sequence( targetSelf, executor ):
      outputs = []
      for rule in targetSelf.rules:
        outputs.append( rule.accept( rule, executor ) )
      
      sequence = [ ]
      for result in outputs:
        sequence += executor( result )
      return sequence
    
    return _Sequence   
    
  def Push( self, target ):      
    def _Push( targetSelf, executor ):
      result = targetSelf.rule.accept( targetSelf.rule, executor )
      return executor( result )
    return _Push
  
  '''def Pull( self, target ):
    def _Pull( targetSelf, executor ):
      result = targetSelf.rule.accept( targetSelf.rule, executor )
      if len(result) > 0:
        raise RuntimeError("Parser returned with fallthrough:" + str(fallthrough) )
      return executor.stack[targetSelf.output]
    return _Pull'''
  
'''class Ordered( RuleCompilerBase ):
  def __init__( self, terminals ):
    super().__init__( terminals )
    
  def Push( self, target ):
    def _Push( targetSelf, executor ):
      return targetSelf.rule.accept( targetSelf.rule, executor )
    return _Push
  
  def Pull( self, target ):
    def _Pull( targetSelf, executor ):
      return targetSelf.rule.accept( targetSelf.rule, executor )
    return _Pull'''
