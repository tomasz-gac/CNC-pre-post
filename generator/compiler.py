from generator.terminal import ParserFailedException

class RuleCompilerBase:
  __slots__ = 'transforms', '_terminals'
  def __init__( self, terminals ):
    self._terminals = terminals
    super().__init__()
  
  def Terminal( self, target ):
    try:
      target.terminal = self._terminals[target.handle]
    except KeyError:
      raise RuntimeError('Parser does not handle terminal '+str(target.handle)) 
    
    def _Terminal( targetSelf, evaluator ):
      result = targetSelf.terminal( evaluator.state )
      return result
    
    return _Terminal
    
  def Handle( self, target ):
    def _Handle( targetSelf, evaluator ):
      return targetSelf.rule.accept( targetSelf.rule, evaluator )
    return _Handle
    
  def Not( self, target ):
    def _Not( targetSelf, evaluator ):
      try:
        result = targetSelf.rule.accept( targetSelf.rule, evaluator )
      except ParserFailedException:
        return []
      
      raise ParserFailedException('Parser marched a Not statement')
    return _Not
    
  def Optional( self, target ):  
    def _Optional( targetSelf, evaluator ):
      save = evaluator.state.save()
      try:        
        return targetSelf.rule.accept( targetSelf.rule, evaluator )
      except ParserFailedException:
        evaluator.state.load( save )
        return []
    return _Optional
  
  def Alternative( self, target ):
    def _Alternative( targetSelf, evaluator ):
      for rule in targetSelf.rules:
        save = evaluator.state.save() # entry evaluator
        try:
          return rule.accept( rule, evaluator )  # try visiting
        except ParserFailedException:
          evaluator.state.load(save) 
      
      raise ParserFailedException('Parser alternative exhausted with no match') # all options exhausted with no match
    return _Alternative
    
  def Sequence( self, target ):
    def _Sequence( targetSelf, evaluator ):
      sequence = [  ]
      for rule in targetSelf.rules:
          # Execute eagerly
        result = rule.accept( rule, evaluator )
        sequence += evaluator( result )
         
      return sequence
    return _Sequence
    
  def Repeat( self, target ):
    def _Repeat( targetSelf, evaluator ):
      sequence = []
      save = None
      try:
        while True:
          save = evaluator.state.save() #save evaluator from before visitation
          sequence += targetSelf.rule.accept( targetSelf.rule, evaluator )
      except ParserFailedException:
        evaluator.state.load( save )  # repeat until failure. Discard failed evaluator
        return sequence
    return _Repeat
    
  def Push( self, target ):
      # Do not execute
    def _Push( targetSelf, evaluator ):
      result = targetSelf.rule.accept( targetSelf.rule, evaluator )
      return result
    return _Push
      
class Reordering( RuleCompilerBase ):
  def __init__( self, terminals ):
    super().__init__( terminals )
    
  def Sequence( self, target ):
      # Start executing after obtaining all of sequence
    def _Sequence( targetSelf, evaluator ):
      outputs = []
      for rule in targetSelf.rules:
        outputs.append( rule.accept( rule, evaluator ) )
      
      sequence = [ ]
      for result in outputs:
        sequence += evaluator( result )
      return sequence
    
    return _Sequence   
    
  def Push( self, target ):      
    def _Push( targetSelf, evaluator ):
      result = targetSelf.rule.accept( targetSelf.rule, evaluator )
      return evaluator( result )
    return _Push