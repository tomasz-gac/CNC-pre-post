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

def angNorm( a ):
  a = a*math.pi/180  
  result = a - (2 * math.pi)*math.floor((a+math.pi)/(2*math.pi))
  return result *180/math.pi
  
def Abs2Inc( value, source, state ):
  incrementalCoord = source.instance.attr.inc
  result = value - state[source]
  if source.instance == Arc.ANG:
    result = angNorm( result )
  result = { incrementalCoord : result }
  # print( 'abs2inc value:%s source:%s result:%s' % (value, source, result))
  return result 

def Inc2Abs( value, source, state ):
  absoluteCoord = source.instance.attr.abs
  result = value + state[absoluteCoord]
  if source.instance == Arc.ANG:
    result = angNorm( result )
  result = { absoluteCoord : result }
  # print( 'inc2abs value:%s source:%s result:%s' % (value, source, result))
  return result


# CIRCLE CENTER X Y Z
class Origin(Morph):  
  class OX(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class OY(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class OZ(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
    
  def __call__( self, member, state ):
    coord2type = { 
      (self.OX.attr.inc, self.OY.attr.inc ) : { Plane.attr.kind : Plane.kind.XY },
      (self.OZ.attr.inc, self.OX.attr.inc ) : { Plane.attr.kind : Plane.kind.ZX },
      (self.OY.attr.inc, self.OZ.attr.inc ) : { Plane.attr.kind : Plane.kind.YZ }
    }
    for (x1, x2), result in coord2type.items():
      if (not math.isclose( x1.value, 0, abs_tol=0.00001 ) and 
          not math.isclose( x2.value, 0, abs_tol=0.00001 ) ):
        return result
    return {}
    

class Plane(Morph):
  origin = Origin
  @unique
  class kind(IntEnum):
    XY = 0
    ZX = 1
    YZ = 2

  
class Point(Morph):
  class X(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class Y(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
  class Z(Morph):
    abs = morphism( float, Abs2Inc )
    inc = morphism( float, Inc2Abs )
    
class Arc(Morph):
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
    Plane.kind.XY : (Point.attr.X,Point.attr.Y,Point.attr.Z),
    Plane.kind.YZ : (Point.attr.Y,Point.attr.Z,Point.attr.X),
    Plane.kind.ZX : (Point.attr.Z,Point.attr.X,Point.attr.Y)
  }
# circle center mappings for polar calculation
planeCenterDict = {  
    Plane.kind.XY : (Origin.attr.OX,Origin.attr.OY),
    Plane.kind.YZ : (Origin.attr.OY,Origin.attr.OZ),
    Plane.kind.ZX : (Origin.attr.OZ,Origin.attr.OX)
  }

class Cartesian(Morph):
  reference = Point
  plane     = Plane
  
  def __call__( self, member, state ):
    # print('cartesian2polar')
    plane  = self.plane.kind
    coord  = planeCoordDict[plane] # get cartesian coordinates for substitution
    center = planeCenterDict[plane]  # get circle center coordinates
    
    x0, x1, x2 = tuple( getattr( self.reference,    x.name).abs for x in coord )
    ox0, ox1   = tuple( getattr( self.plane.origin, x.name).abs for x in center )
    
    r1, r2 = (x0-ox0), (x1-ox1)
    
    result = {}
    result[ Arc.RAD.attr.abs ] = math.sqrt(r1**2 + r2**2)
    result[ Arc.ANG.attr.abs ] = angNorm( math.atan2(r2, r1)* float(180)/math.pi )
    result[ Arc.LEN.attr.abs ] = x2
    inc_results = [ Abs2Inc(value, key, state).items() for key,value in result.items() ]
    result.update( pair for list in inc_results for pair in list )
    result[Polar.attr.plane] = self.plane
    obj = construct( Polar, result )
    
    return { Position.attr.polar : obj }
    
class Polar(Morph):
  reference = Arc
  plane     = Plane
    
  def __call__( self, member, state ):
    # print('polar2cartesian')
    plane  = self.plane.kind
    coord  = planeCoordDict[plane]   # get cartesian coordinates for substitution
    center = planeCenterDict[plane]  # get circle center coordinates
    
    x0, x1, x2 = tuple( x.value.attr.abs for x in coord )
    cx0, cx1   = tuple( getattr( self.plane.origin, x.name).abs for x in center )
    
    result = {}
    result[ x0 ] = cx0 + self.reference.RAD.abs*math.cos(self.reference.ANG.abs*math.pi/180)
    result[ x1 ] = cx1 + self.reference.RAD.abs*math.sin(self.reference.ANG.abs*math.pi/180)
    result[ x2 ] = self.reference.LEN.abs
    inc_results = [ Abs2Inc(value, key, state).items() for key,value in result.items() ]
    result.update( pair for list in inc_results for pair in list )
    result[Cartesian.attr.plane] = self.plane
    obj = construct( Cartesian, result )
    
    return { Position.attr.cartesian : obj }
    
class Position(Morph):
  cartesian = Cartesian
  polar     = Polar
  
def StateDict():
  result = { key : 0 for key in list(Registers) }
  result.update( { kind : 0 for key in Point.attr for kind in key.value.attr } )
  result.update( { kind : 0 for key in Arc.attr     for kind in key.value.attr } )
  result.update( { kind : 0 for key in Angular.attr   for kind in key.value.attr } )
  result.update( { kind : 0 for key in Origin.attr  for kind in key.value.attr } )  
  result[Registers.COMPENSATION] = Compensation.NONE
  result[Registers.DIRECTION]    = Direction.CW
  result[Registers.UNITS]        = Units.MM
  result[Registers.MOTIONMODE]   = Motion.LINEAR
  result[Registers.WCS]          = 54
  result[Plane.attr.kind]        = Plane.kind.XY
  result[Registers.COOLANT]      = Coolant.OFF
  return result