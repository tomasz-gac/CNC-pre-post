        
class Setval: # Setval(B, A) -> B = A
  def __init__( self, attribute, value ):
    self.attribute = attribute
    self.value = value
  def __call__( self, state ):
    state.symtable[self.attribute] = self.value
  def __repr__( self ):
    return 'setval: '+self.attribute.__repr__()+' = '+self.value.__repr__()

class Set:  # A Set(B) -> B = A
  def __init__(self, attribute):
    self.attribute = attribute
    
  def __call__( self, state ):
    state.symtable[self.attribute] = state.stack[-1]
    del state.stack[-1]
    
  def __repr__( self ):
    return 'Set (' + self.attribute.__repr__() + ')'
      
class Temporary:  # SET REGISTER VALUE AS TEMPORARY AND RESTORE IT AFTER INVARIANT
  def __init__(self, attribute ):
    self.attribute = attribute
    
  def __call__( self, state ):
    state.symtable['temporary'] = self.attribute
  
  def __repr__( self ):
    return 'Temporary: '+self.attribute.__repr__()
    
def stop( state ):  # PROGRAM STOP
  pass
  
def optionalStop( state ):  # PROGRAM OPTIONAL STOP
  pass

def toolchange( state ):  # CHANGE TOOL TO Registers.TOOLNO
  pass
  
def end( state ): # END PROGRAM
  pass

def discard( state ): # DISCARD STATE BUFFER
  del state.stack[:]

def invariant( state ):
  pass
  
  
# GOTO command requires 3 target coordinates
# This function handles the missing coordinates if the the user provided less
# It supplies the missing coordinates depending on the specified 'kind'
# by defaulting the incremental counterparts to zero
class SetGOTODefaults:
  def __init__( self, coordinates ):
    self.coordinates = coordinates
  def __call__( self, state ):
      # For each coordinate in 'self.coordinates'
      # that is  missing from state.symtable
      # set its incremental counterpart to 0
    constants = { coord.value.attr.inc : 0 for coord in self.coordinates.attr if coord.value.attr.abs not in state.symtable }
      # In case the user already specified incremental coordinates in symtable,
      # update constants with symtable to override conflicts
    constants.update( state.symtable )
    state.symtable = constants