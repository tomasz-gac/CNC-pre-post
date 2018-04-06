class Stack2args:
  def __init__(self, function , nargs ):
    self.function = function
    self.nargs    = nargs
    
  def __call__( self, state ):
    args = state.stack[-self.nargs:]
    del state.stack[-self.nargs:]
    state.stack += self.function( state, *args )
    
  def __repr__( self ):
    return ' <Stack2args(' + str(self.function) + ',' + str(self.nargs) + ')>'
    
    
# Convert handler function from signature (state) to (state, a1, a2, ..., aNargs)    
def stack2args( nargs ):
  def decorate( fn ):
    return Stack2args( fn, nargs )
  return decorate

class Evaluator:
  def __init__( self ):
    self.stack = []
     
  def __call__( self, expression ):
    for command in expression:
      command( self )
    return self