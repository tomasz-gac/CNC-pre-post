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
      # Do nothing
    return children[0]
    
  def Not( self, target, children ):
    def _Not( state ):
      try:
        result = children[0]( state )
      except ParserFailedException:
        return []
      
      raise ParserFailedException('Parser marched a Not statement')
    return _Not
    
  def Optional( self, target, children ):  
    def _Optional( state ):
      save = state.save()
      try:        
        return children[0]( state )
      except ParserFailedException:
        state.load( save )
        return []
    return _Optional
  
  def Alternative( self, target, children ):
    def _Alternative( state ):
      for rule in children:
        save = state.save() # entry state
        try:
          return rule( state )  # try visiting
        except ParserFailedException:
          state.load(save) 
      
      raise ParserFailedException('Parser alternative exhausted with no match') # all options exhausted with no match
    return _Alternative
    
  def Sequence( self, target, children ):
    def _Sequence( state ):
      # sequence = [  ]
      # for rule in children:
      list( f(state) for f in rule( state ) for rule in children ) # call parser result on state for each element
      
      return []# sequence
    return _Sequence
    
  def Repeat( self, target, children ):
    def _Repeat( state ):
      sequence = []
      save = None
      try:
        while True:
          save = state.save() #save state from before visitation
          sequence.extend( children[0]( state ) )
      except ParserFailedException:
        state.load( save )  # repeat until failure. Discard failed state
        return sequence
    return _Repeat
    
  def Push( self, target, children ):
      # Do nothing
    return children[0]
      
class Reordering( RuleCompilerBase ):
  def __init__( self, terminals ):
    super().__init__( terminals )
    
  def Sequence( self, target, children ):
      # Start executing after obtaining all of sequence
    def _Sequence( state ):
      sequence = []
      for rule in children:
        sequence.extend( rule( state ) )
      
      lst = [ f(state) for f in sequence ]
      return []
    
    return _Sequence   
    
  def Push( self, target, children ):      
    def _Push( state ):
      result = children[0]( state )
      lst = [ f(state) for f in result ]
      return []
    return _Push