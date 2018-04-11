from generator.terminal import ParserFailedException

class RuleCompilerBase:
  __slots__ = 'transforms', '_terminals'
  def __init__( self, terminals ):
    self._terminals = terminals
    super().__init__()
  
  def Terminal( self, target, children ):
    try:
      return self._terminals[target.handle]
    except KeyError:
      raise RuntimeError('Missing terminal during compilation: '+str(target.handle))
    
  def Handle( self, target, children ):
    return children[0]
    
  def Not( self, target, children ):
    def _Not( evaluator ):
      try:
        result = children[0]( evaluator )
      except ParserFailedException:
        return []
      
      raise ParserFailedException('Parser marched a Not statement')
    return _Not
    
  def Optional( self, target, children ):  
    def _Optional( evaluator ):
      save = evaluator.state.save()
      try:        
        return children[0]( evaluator )
      except ParserFailedException:
        evaluator.state.load( save )
        return []
    return _Optional
  
  def Alternative( self, target, children ):
    def _Alternative( evaluator ):
      for rule in children:
        save = evaluator.state.save() # entry state
        try:
          return rule( evaluator )  # try visiting
        except ParserFailedException:
          evaluator.state.load(save) 
      
      raise ParserFailedException('Parser alternative exhausted with no match') # all options exhausted with no match
    return _Alternative
    
  def Sequence( self, target, children ):
    def _Sequence( evaluator ):
      sequence = [  ]
      for rule in children:
        sequence.extend( evaluator( rule( evaluator ) ) ) # Execute in order
         
      return sequence
    return _Sequence
    
  def Repeat( self, target, children ):
    def _Repeat( evaluator ):
      sequence = []
      save = None
      try:
        while True:
          save = evaluator.state.save() #save evaluator from before visitation
          sequence.extend( children[0]( evaluator ) )
      except ParserFailedException:
        evaluator.state.load( save )  # repeat until failure. Discard failed evaluator
        return sequence
    return _Repeat
    
  def Push( self, target, children ):
      # Do not execute
    def _Push( evaluator ):
      result = children[0]( evaluator )
      return result
    return _Push
      
class Reordering( RuleCompilerBase ):
  def __init__( self, terminals ):
    super().__init__( terminals )
    
  def Sequence( self, target, children ):
      # Start executing after obtaining all of sequence
    def _Sequence( evaluator ):
      sequence = []
      for rule in children:
        sequence.extend( rule( evaluator ) )
      
      return evaluator( sequence )
    
    return _Sequence   
    
  def Push( self, target, children ):      
    def _Push( evaluator ):
      result = children[0]( evaluator )
      return evaluator( result )
    return _Push