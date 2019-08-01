from enum import Enum, IntEnum, unique
from languages.heidenhain.type import Morph, MorphMeta, morphism
import math
  
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
  return value.cls.incremental[value.name]
  
def inc2abs( value ):
  return value.cls.absolute[value.name]
  
def Abs2Inc( value, source, state ):
    return { abs2inc(source) : value - state[source] }

def Inc2Abs( value, source, state ):
    return { inc2abs(source) : value + state[source] }
    
def makeIncremental( absolute, incremental ):
  absolute.incremental = incremental
  incremental.absolute = absolute

class Cartesian(Morph):
  X = morphism( float, Abs2Inc )
  Y = morphism( float, Abs2Inc )
  Z = morphism( float, Abs2Inc )
  
  def __call__( self, member, state ):
    return cartesian2polar( self, member, state )
  
class Polar(Morph):
  ANG = morphism( float, Abs2Inc )
  RAD = morphism( float, Abs2Inc )
  LEN = morphism( float, Abs2Inc )
  
  def __call__( self, member, state ):
    return polar2cartesian( self, member, state )
    
class Angular(Morph):
  A = morphism( float, Abs2Inc )
  B = morphism( float, Abs2Inc )
  C = morphism( float, Abs2Inc )

class Center(Morph): # CIRCLE CENTER X Y Z
  X = morphism( float, Abs2Inc )
  Y = morphism( float, Abs2Inc )
  Z = morphism( float, Abs2Inc )

class CartesianInc(Morph):
  X = morphism( float, Inc2Abs )
  Y = morphism( float, Inc2Abs )
  Z = morphism( float, Inc2Abs )

class PolarInc(Morph):
  ANG = morphism( float, Inc2Abs )
  RAD = morphism( float, Inc2Abs )
  LEN = morphism( float, Inc2Abs )

class AngularInc(Morph):
  A = morphism( float, Inc2Abs )
  B = morphism( float, Inc2Abs )
  C = morphism( float, Inc2Abs )

class CenterInc(Morph):
  X = morphism( float, Inc2Abs )
  Y = morphism( float, Inc2Abs )
  Z = morphism( float, Inc2Abs )

makeIncremental( Cartesian, CartesianInc )  
makeIncremental( Polar, PolarInc )
makeIncremental( Angular, AngularInc )
makeIncremental( Center, CenterInc )

class Cart(Morph):
  absolute    = Cartesian
  incremental = CartesianInc
  
class Pol( Morph ):
  absolute    = Polar
  incremental = PolarInc

class Ang( Morph ):
  absolute    = Angular
  incremental = AngularInc

class Cent( Morph ):
  absolute    = Center
  incremental = CenterInc
  
class Position( Morph ):
  cartesian = Cart
  polar     = Pol
  angular   = Ang
  center    = Cent
   
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
      state = StateDict()
    
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
    
planeCoordDict = {  
    Plane.XY : (Cartesian.X,Cartesian.Y,Cartesian.Z),
    Plane.YZ : (Cartesian.Y,Cartesian.Z,Cartesian.X),
    Plane.ZX : (Cartesian.Z,Cartesian.X,Cartesian.Y)
  }
# circle center mappings for polar calculation
planeCenterDict = {  
    Plane.XY : (Center.X,Center.Y),
    Plane.YZ : (Center.Y,Center.Z),
    Plane.ZX : (Center.Z,Center.X)
  }

def angNorm( a ):
  # ang = (a+2*math.pi) % (2 * math.pi)
  return a - (2 * math.pi)*math.floor((a+math.pi)/(2*math.pi))
  
def cartesian2polar( self, member, state ):
  plane = state[Registers.POLARPLANE]
  x1, x2, x3 = planeCoordDict[plane] # get cartesian coordinates for substitution
  cx1, cx2 = planeCenterDict[plane]  # get circle center coordinates
  
  r1, r2 = (getattr( self, x1.name)-state[cx1]), (getattr( self, x2.name)-state[cx2])
  
  result = {}
  result[ Polar.RAD ] = math.sqrt(r1**2 + r2**2)
  result[ Polar.ANG ] = angNorm(math.atan2(r2, r1)) * float(180)/math.pi
  result[ Polar.LEN ] = getattr(self, x3.name )
  return result
  
def polar2cartesian( self, member, state ):
  plane = state[Registers.POLARPLANE]
  x1, x2, x3  = planeCoordDict[plane]   # get cartesian coordinates for substitution
  cx1, cx2    = planeCenterDict[plane]  # get circle center coordinates
  
  result = {}
  result[ x1 ] = state[ cx1 ] + self.RAD*math.cos(self.ANG*math.pi/180)
  result[ x2 ] = state[ cx2 ] + self.RAD*math.sin(self.ANG*math.pi/180)
  result[ x3 ] = self.LEN
  
  return result