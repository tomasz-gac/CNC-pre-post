from enum import Enum, IntEnum, unique
from hydra import Morph, morphism, construct
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
  
def abs2inc( value ):
  return value.instance.attr.inc
  
def inc2abs( value ):
  return value.instance.attr.abs
  
def Abs2Inc( value, source, state ):
  incrementalCoord = abs2inc(source)
  result = { incrementalCoord : value - state[source] }
  # print( 'abs2inc value:%s source:%s result:%s' % (value, source, result))
  return result 

def Inc2Abs( value, source, state ):
  absoluteCoord = inc2abs(source)
  result = { absoluteCoord : value + state[absoluteCoord] }
  # print( 'inc2abs value:%s source:%s result:%s' % (value, source, result))
  return result

# CIRCLE CENTER X Y Z
class Center(Morph):  
  class CX(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class CY(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class CZ(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  
  
class Cartesian(Morph):
  class X(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class Y(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class Z(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
    
class Polar(Morph):
  class RAD(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class ANG(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class LEN(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )

class Angular(Morph):
  class A(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class B(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class C(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )

planeCoordDict = {  
    Plane.XY : (Cartesian.attr.X,Cartesian.attr.Y,Cartesian.attr.Z),
    Plane.YZ : (Cartesian.attr.Y,Cartesian.attr.Z,Cartesian.attr.X),
    Plane.ZX : (Cartesian.attr.Z,Cartesian.attr.X,Cartesian.attr.Y)
  }
# circle center mappings for polar calculation
planeCenterDict = {  
    Plane.XY : (Center.attr.CX,Center.attr.CY),
    Plane.YZ : (Center.attr.CY,Center.attr.CZ),
    Plane.ZX : (Center.attr.CZ,Center.attr.CX)
  }
    
def angNorm( a ):
  # ang = (a+2*math.pi) % (2 * math.pi)
  return a - (2 * math.pi)*math.floor((a+math.pi)/(2*math.pi))

class Cartesian2Polar(Morph):
  cartesian = Cartesian
  center    = Center
  
  def __call__( self, member, state ):
    # print('cartesian2polar')
    plane  = state[Registers.POLARPLANE]
    coord  = planeCoordDict[plane] # get cartesian coordinates for substitution
    center = planeCenterDict[plane]  # get circle center coordinates
    
    x0, x1, x2 = tuple( getattr( self.cartesian, x.name).abs for x in coord )
    cx0, cx1   = tuple( getattr( self.center,    x.name).abs for x in center )
    
    r1, r2 = (x0-cx0), (x1-cx1)
    
    result = {}
    result[ Polar.RAD.attr.abs ] = math.sqrt(r1**2 + r2**2)
    result[ Polar.ANG.attr.abs ] = angNorm(math.atan2(r2, r1)) * float(180)/math.pi
    result[ Polar.LEN.attr.abs ] = x2
    inc_results = ( Abs2Inc(value, key, state).items() for key,value in result.items() )
    result.update( pair for list in inc_results for pair in list )
    result[Polar2Cartesian.attr.center] = self.center
    obj = construct( Polar2Cartesian, result )
    
    return { Position.attr.polar : obj }
    
class Polar2Cartesian(Morph):
  polar  = Polar
  center = Center
    
  def __call__( self, member, state ):
    # print('polar2cartesian')
    plane = state[Registers.POLARPLANE]
    coord  = planeCoordDict[plane]   # get cartesian coordinates for substitution
    center = planeCenterDict[plane]  # get circle center coordinates
    
    x0, x1, x2 = tuple( x.value.attr.abs for x in coord )
    cx0, cx1 = tuple( getattr( self.center, x.name).abs for x in center )
    
    result = {}
    result[ x0 ] = cx0 + self.polar.RAD.abs*math.cos(self.polar.ANG.abs*math.pi/180)
    result[ x1 ] = cx1 + self.polar.RAD.abs*math.sin(self.polar.ANG.abs*math.pi/180)
    result[ x2 ] = self.polar.LEN.abs
    inc_results = ( Abs2Inc(value, key, state).items() for key,value in result.items() )
    result.update( pair for list in inc_results for pair in list )
    result[Cartesian2Polar.attr.center] = self.center
    obj = construct( Cartesian2Polar, result )
    # print(result)
    return { Position.attr.cartesian : obj }
    
class Position(Morph):
  cartesian = Cartesian2Polar
  polar     = Polar2Cartesian

def StateDict():
  result = { key : 0 for key in list(Registers) }
  result.update( { kind : 0 for key in Cartesian.attr for kind in key.value.attr } )
  result.update( { kind : 0 for key in Polar.attr     for kind in key.value.attr } )
  result.update( { kind : 0 for key in Angular.attr   for kind in key.value.attr } )
  result.update( { kind : 0 for key in Center.attr    for kind in key.value.attr } )
  result[Registers.COMPENSATION] = Compensation.NONE
  result[Registers.DIRECTION]    = Direction.CW
  result[Registers.UNITS]        = Units.MM
  result[Registers.MOTIONMODE]   = Motion.LINEAR
  result[Registers.WCS]          = 54
  result[Registers.POLARPLANE]   = Plane.XY
  result[Registers.COOLANT]      = Coolant.OFF
  return result
        
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