from enum import Enum, IntEnum, unique
from languages.heidenhain.type import Morph
  
@unique
class Registers(IntEnum):
  COMPENSATION = 0   # COMPENSATION TYPE
  DIRECTION    = 1   # CIRCLE DIRECTION
  LINENO       = 2   # LINE NUMBER
  UNITS        = 3   # MACHINE UNITS
  FEED         = 4   # MACHINE FEED
  SPINSPEED    = 5   # SPINDLE SPEED
  SPINDIR      = 6   # SPINDLE ROTATION DIRECTION
  MOTIONMODE   = 7   # POSITIONING MOTION MODE
  TOOLNO       = 8   # TOOL NUMBER
  TOOLDL       = 9   # TOOL DELTA LENGTH
  TOOLDR       = 10  # TOOL DELTA RADIUS
  COOLANT      = 11  # COOLANT TYPE
  WCS          = 12  # WORLD COORDINATE SYSTEM NUMBER
  POLARPLANE   = 13  # POLAR MOTION PLANE
  
def isAbsolute( coord ):
  return hasattr( coord, 'incremental' )
  
def isIncremental( coord ):
  return hasattr( coord, 'absolute' )
  
def abs2inc( value ):
  return value.type.incremental[value.name]
  
def inc2abs( value ):
  return value.type.absolute[value.name]
  
def Abs2Inc( source, value, state ):
    return { abs2inc(source) : value - state[source] }

def Inc2Abs( source, value, state ):
    return { inc2abs(source) : value + state[source] }

'''class Abs2Inc(Morph):
  def __call__( self, source, value, state ):
    return { abs2inc(source) : value - state[source] }

class Inc2Abs(Morph):
  def __call__( self, source, value, state ):
    return { inc2abs(source) : value + state[source] }'''
    
def makeIncremental( absolute, incremental ):
  absolute.incremental = incremental
  incremental.absolute = absolute
  # return result

    
class Cartesian(Morph):
  X = Abs2Inc
  Y = Abs2Inc
  Z = Abs2Inc
    
  
class Polar(Morph):
  ANG = Abs2Inc
  RAD = Abs2Inc
  LEN = Abs2Inc
    
class Angular(Morph):
  A = Abs2Inc
  B = Abs2Inc
  C = Abs2Inc

class Center(Morph): # CIRCLE CENTER X Y Z
  X = Abs2Inc
  Y = Abs2Inc
  Z = Abs2Inc

class CartesianInc(Morph):
  X = Inc2Abs
  Y = Inc2Abs
  Z = Inc2Abs

class PolarInc(Morph):
  ANG = Inc2Abs
  RAD = Inc2Abs
  LEN = Inc2Abs

class AngularInc(Morph):
  A = Inc2Abs
  B = Inc2Abs
  C = Inc2Abs

class CenterInc(Morph):
  X = Inc2Abs
  Y = Inc2Abs
  Z = Inc2Abs

makeIncremental( Cartesian, CartesianInc )  
makeIncremental( Polar, PolarInc )
makeIncremental( Angular, AngularInc )
makeIncremental( Center, CenterInc )

class Cart(Morph):
  absolute    = Cartesian
  incremental = CartesianInc



 
@unique
class Units(IntEnum):
  MM    = 0
  INCH  = 1
  
@unique
class Compensation(IntEnum):
  NONE = 0
  LEFT = 1
  RIGHT = 2

@unique
class Direction(IntEnum):
  CW = 0
  CCW = 1
  
@unique
class Motion(IntEnum):
  LINEAR = 0
  CIRCULAR = 1
  
@unique
class Coolant(IntEnum):
  OFF   = 0
  FLOOD = 1
  MIST  = 2
  AIR   = 3
  
@unique
class Spindle(IntEnum):
  OFF = 0
  CW  = 1
  CCW = 2
  
@unique
class Plane(IntEnum):
  XY = 0
  ZX = 1
  YZ = 2

def StateDict():
  result = { key : 0 for key in list(Registers) }
  result.update( { key : 0 for key in list(Cartesian)} )
  result.update( { key : 0 for key in list(CartesianInc)} )
  result.update( { key : 0 for key in list(Polar) } )
  result.update( { key : 0 for key in list(PolarInc) } )
  result.update( { key : 0 for key in list(Angular) } )
  result.update( { key : 0 for key in list(AngularInc) } )
  result.update( { key : 0 for key in list(Center) } )
  result.update( { key : 0 for key in list(CenterInc) } )
  result[Registers.COMPENSATION] = Compensation.NONE
  result[Registers.DIRECTION]    = Direction.CW
  result[Registers.UNITS]        = Units.MM
  result[Registers.MOTIONMODE]   = Motion.LINEAR
  result[Registers.WCS]          = 54
  result[Registers.POLARPLANE]   = Plane.XY
  result[Registers.COOLANT]      = Coolant.OFF
  return result

class MachineState:
  __slots__ = 'registers', 'cartesian', 'polar', 'angular', 'center'
  def __init__( self, state=None ):
    if state is None:
      state = cmd.StateDict()
    
    self.registers = {}
    self.cartesian = {}
    self.polar     = {}
    self.angular   = {}
    self.center    = {}
    vars = { 
      Registers : self.registers,
      Cartesian : self.cartesian,  
      Polar     : self.polar,
      Angular   : self.angular,
      Center    : self.center
    }
    for key, item in state.items():
      vars[type(key)][key] = item
        
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
# This function handles the missing coordinates if the the user provided fewer
# It supplies the missing coordinates depending on the specified 'kind'
# by defaulting the incremental counterparts to zero
class SetGOTODefaults:
  def __init__( self, coordinates ):
    if isIncremental(coordinates):
      raise RuntimeError('Expected absolute coordinate enum, got: '+str(coordinates))
    self.coordinates = coordinates
  def __call__( self, state ):
      # For each coordinate in 'self.coordinates'
      # that is  missing from state.symtable
      # set its incremental counterpart to 0
    constants = { abs2inc(abs) : 0 for abs in self.coordinates if abs not in state.symtable }
      # In case the user already specified incremental coordinates in symtable,
      # update constants with symtable to override conflicts
    constants.update( state.symtable )
    state.symtable = constants