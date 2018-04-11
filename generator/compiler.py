from generator.terminal import ParserFailedException

class RuleCompilerBase:
  __slots__ = 'transforms', '_terminals'
  def __init__( self, terminals ):
    self._terminals = terminals
    super().__init__()
  
  def Terminal( self, target, child_methods ):
    try:
      return self._terminals[target.handle]
    except KeyError:
      raise RuntimeError('Missing terminal during compilation: '+str(target.handle))
    
  def Handle( self, target, child_methods ):
    def _Handle( evaluator ):
      return child_methods[0]( evaluator )
    return _Handle
    
  def Not( self, target, child_methods ):
    def _Not( evaluator ):
      try:
        result = child_methods[0]( evaluator )
      except ParserFailedException:
        return []
      
      raise ParserFailedException('Parser marched a Not statement')
    return _Not
    
  def Optional( self, target, child_methods ):  
    def _Optional( evaluator ):
      save = evaluator.state.save()
      try:        
        return child_methods[0]( evaluator )
      except ParserFailedException:
        evaluator.state.load( save )
        return []
    return _Optional
  
  def Alternative( self, target, child_methods ):
    def _Alternative( evaluator ):
      for rule in child_methods:
        save = evaluator.state.save() # entry evaluator
        try:
          return rule( evaluator )  # try visiting
        except ParserFailedException:
          evaluator.state.load(save) 
      
      raise ParserFailedException('Parser alternative exhausted with no match') # all options exhausted with no match
    return _Alternative
    
  def Sequence( self, target, child_methods ):
    def _Sequence( evaluator ):
      sequence = [  ]
      for rule in child_methods:
          # Execute eagerly
        sequence.extend( evaluator( rule( evaluator ) ) )
         
      return sequence
    return _Sequence
    
  def Repeat( self, target, child_methods ):
    def _Repeat( evaluator ):
      sequence = []
      save = None
      try:
        while True:
          save = evaluator.state.save() #save evaluator from before visitation
          sequence.extend( child_methods[0]( evaluator ) )
      except ParserFailedException:
        evaluator.state.load( save )  # repeat until failure. Discard failed evaluator
        return sequence
    return _Repeat
    
  def Push( self, target, child_methods ):
      # Do not execute
    def _Push( evaluator ):
      result = child_methods[0]( evaluator )
      return result
    return _Push
      
class Reordering( RuleCompilerBase ):
  def __init__( self, terminals ):
    super().__init__( terminals )
    
  def Sequence( self, target, child_methods ):
      # Start executing after obtaining all of sequence
    def _Sequence( evaluator ):
      sequence = []
      for rule in child_methods:
        sequence.extend( rule( evaluator ) )
      
      return evaluator( sequence )
    
    return _Sequence   
    
  def Push( self, target, child_methods ):      
    def _Push( evaluator ):
      result = child_methods[0]( evaluator )
      return evaluator( result )
    return _Push