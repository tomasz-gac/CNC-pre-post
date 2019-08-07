from enum import Enum, IntEnum, unique
from hydra import Morph, morphism
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
  return getattr( value.instance.incremental.attr, value.name )
  
def inc2abs( value ):
  return getattr( value.instance.absolute.attr, value.name )
  
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
    
def associate_absinc( absolute, incremental ):
  absolute.incremental = incremental
  incremental.absolute = absolute

class CenterAbs(Morph): # CIRCLE CENTER X Y Z
  X = morphism( float, Abs2Inc )
  Y = morphism( float, Abs2Inc )
  Z = morphism( float, Abs2Inc )
  
class CenterInc(Morph):
  X = morphism( float, Inc2Abs )
  Y = morphism( float, Inc2Abs )
  Z = morphism( float, Inc2Abs )

associate_absinc( CenterAbs, CenterInc )
class Center(Morph):  
  absolute    = CenterAbs
  incremental = CenterInc
  
  
class Cartesian(Morph):
  class absolute(Morph):
    X = morphism( float, Abs2Inc )
    Y = morphism( float, Abs2Inc )
    Z = morphism( float, Abs2Inc )
  
  class incremental(Morph):
    X = morphism( float, Inc2Abs )
    Y = morphism( float, Inc2Abs )
    Z = morphism( float, Inc2Abs )
  
  center = Center
  
  def __call__( self, member, state ):
      return cartesian2polar( self, member, state )

associate_absinc( Cartesian.absolute, Cartesian.incremental )
    
class Polar(Morph):
  class absolute(Morph):
    ANG = morphism( float, Abs2Inc )
    RAD = morphism( float, Abs2Inc )
    LEN = morphism( float, Abs2Inc )

  class incremental(Morph):
    ANG = morphism( float, Inc2Abs )
    RAD = morphism( float, Inc2Abs )
    LEN = morphism( float, Inc2Abs )
    
  center = Center
    
  def __call__( self, member, state ):
    return polar2cartesian( self, member, state )
    

associate_absinc( Polar.absolute, Polar.incremental )


class Angular(Morph):
  class absolute(Morph):
    A = morphism( float, Abs2Inc )
    B = morphism( float, Abs2Inc )
    C = morphism( float, Abs2Inc )
  class incremental(Morph):
    A = morphism( float, Inc2Abs )
    B = morphism( float, Inc2Abs )
    C = morphism( float, Inc2Abs )

associate_absinc( Angular.absolute, Angular.incremental )
   
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
  result.update( { key : 0 for key in Cartesian.absolute.attr} )
  result.update( { key : 0 for key in Cartesian.incremental.attr} )
  result.update( { key : 0 for key in Polar.absolute.attr } )
  result.update( { key : 0 for key in Polar.incremental.attr } )
  result.update( { key : 0 for key in Angular.absolute.attr } )
  result.update( { key : 0 for key in Angular.incremental.attr } )
  result.update( { key : 0 for key in Center.absolute.attr } )
  result.update( { key : 0 for key in Center.incremental.attr } )
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
    if isIncremental(coordinates):
      raise RuntimeError('Expected absolute coordinate enum, got: '+str(coordinates))
    self.coordinates = coordinates
  def __call__( self, state ):
      # For each coordinate in 'self.coordinates'
      # that is  missing from state.symtable
      # set its incremental counterpart to 0
    constants = { abs2inc(abs) : 0 for abs in self.coordinates.attr if abs not in state.symtable }
      # In case the user already specified incremental coordinates in symtable,
      # update constants with symtable to override conflicts
    constants.update( state.symtable )
    state.symtable = constants
    
planeCoordDict = {  
    Plane.XY : (Cartesian.absolute.attr.X,Cartesian.absolute.attr.Y,Cartesian.absolute.attr.Z),
    Plane.YZ : (Cartesian.absolute.attr.Y,Cartesian.absolute.attr.Z,Cartesian.absolute.attr.X),
    Plane.ZX : (Cartesian.absolute.attr.Z,Cartesian.absolute.attr.X,Cartesian.absolute.attr.Y)
  }
# circle center mappings for polar calculation
planeCenterDict = {  
    Plane.XY : (Center.absolute.attr.X,Center.absolute.attr.Y),
    Plane.YZ : (Center.absolute.attr.Y,Center.absolute.attr.Z),
    Plane.ZX : (Center.absolute.attr.Z,Center.absolute.attr.X)
  }

def angNorm( a ):
  # ang = (a+2*math.pi) % (2 * math.pi)
  return a - (2 * math.pi)*math.floor((a+math.pi)/(2*math.pi))
  
def cartesian2polar( self, member, state ):
  print('cartesian2polar')
  plane = state[Registers.POLARPLANE]
  x1, x2, x3 = planeCoordDict[plane] # get cartesian coordinates for substitution
  cx1, cx2 = planeCenterDict[plane]  # get circle center coordinates
  
  r1, r2 = (getattr( self.absolute, x1.name)-state[cx1]), (getattr( self.absolute, x2.name)-state[cx2])
  
  result = {}
  result[ Polar.absolute.attr.RAD ] = math.sqrt(r1**2 + r2**2)
  result[ Polar.absolute.attr.ANG ] = angNorm(math.atan2(r2, r1)) * float(180)/math.pi
  result[ Polar.absolute.attr.LEN ] = getattr(self.absolute, x3.name )
  print(result)
  return result
  
def polar2cartesian( self, member, state ):
  print('polar2cartesian')
  plane = state[Registers.POLARPLANE]
  x1, x2, x3  = planeCoordDict[plane]   # get cartesian coordinates for substitution
  cx1, cx2    = planeCenterDict[plane]  # get circle center coordinates
  
  result = {}
  result[ x1 ] = state[ cx1 ] + self.absolute.RAD*math.cos(self.absolute.ANG*math.pi/180)
  result[ x2 ] = state[ cx2 ] + self.absolute.RAD*math.sin(self.absolute.ANG*math.pi/180)
  result[ x3 ] = self.absolute.LEN  
  print(result)
  return result