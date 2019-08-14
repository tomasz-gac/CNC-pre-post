from enum import Enum, IntEnum, unique
from hydra import Morph, morphism, construct
import math

@unique
class Registers(IntEnum):
  LINENO       = 2   # LINE NUMBER
  UNITS        = 3   # MACHINE UNITS
  WCS          = 12  # WORLD COORDINATE SYSTEM NUMBER
  
@unique
class Units(IntEnum):
  MM    = 0
  INCH  = 1

# Normalize angle to be contained between 0 and 360 degress
def angNorm( a ):
  a = a*math.pi/180  
  result = a - (2 * math.pi)*math.floor((a+math.pi)/(2*math.pi))
  return result *180/math.pi

# Calculate the incremental value given absolute coordinate
def Abs2Inc( value, source, state ):
  incrementalCoord = source.instance.attr.inc
  result = value - state[source]
  if source.instance == Arc.ANG:
    result = angNorm( result )
  result = { incrementalCoord : result }
  # print( 'abs2inc value:%s source:%s result:%s' % (value, source, result))
  return result 
  
# Calculate the absolute value given incremental coordinate
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
    
  ''' Calculate the plane type depending on specified coordinates '''
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
    
# Plane for polar and cartesian coordinate system calculations
class Plane(Morph):
  origin = Origin
  @unique
  class kind(IntEnum):
    XY = 0
    ZX = 1
    YZ = 2

# Cartesian coordinate system reference
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

# Polar coordinate system reference
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

# For 5-axis machines
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

# circle center mappings for polar-cartesian translation
planeCoordDict = {  
    Plane.kind.XY : (Point.attr.X,Point.attr.Y,Point.attr.Z),
    Plane.kind.YZ : (Point.attr.Y,Point.attr.Z,Point.attr.X),
    Plane.kind.ZX : (Point.attr.Z,Point.attr.X,Point.attr.Y)
  }
planeCenterDict = {  
    Plane.kind.XY : (Origin.attr.OX,Origin.attr.OY),
    Plane.kind.YZ : (Origin.attr.OY,Origin.attr.OZ),
    Plane.kind.ZX : (Origin.attr.OZ,Origin.attr.OX)
  }
# Cartesian coordinate system
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

# Polar coordinate system
class Polar(Morph):
  reference = Arc
  plane     = Plane
  
  ''' Calculates the position in the cartesian coordinate system 
      given the Arc reference and circle plane. '''
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

# Tool position
class Position(Morph):
  cartesian = Cartesian
  polar     = Polar

class Spindle(Morph):
  speed = float         # SPINDLE SPEED
  tool  = int           # TOOL NUMBER
  DL    = float         # TOOL DELTA LENGTH
  DR    = float         # TOOL DELTA RADIUS
  @unique
  class spindir(IntEnum):
    OFF = 0
    CW  = 1
    CCW = 2
  @unique
  class coolant(IntEnum):     # COOLANT TYPE
    OFF   = 0
    FLOOD = 1
    MIST  = 2
    AIR   = 3

# Motion
class Motion(Morph):
  target  = Position
  spindle = Spindle
  feed    = float     # MACHINE FEED
  
  @unique
  class compensation(IntEnum):  # COMPENSATION TYPE
    NONE = 0
    LEFT = 1
    RIGHT = 2
  @unique
  class direction(IntEnum):     # CIRCLE DIRECTION
    CW = 0
    CCW = 1
  @unique
  class mode(IntEnum):          # POSITIONING MOTION MODE
    LINEAR = 0
    CIRCULAR = 1

def StateDict():
  pool = { key : 0 for key in list(Registers) }
  pool.update( { kind : 0 for key in Point.attr for kind in key.value.attr } )
  pool.update( { kind : 0 for key in Arc.attr     for kind in key.value.attr } )
  pool.update( { kind : 0 for key in Angular.attr   for kind in key.value.attr } )
  pool.update( { kind : 0 for key in Origin.attr  for kind in key.value.attr } )  
  pool[Motion.attr.feed]         = 100
  pool[Motion.attr.compensation] = Motion.compensation.NONE
  pool[Motion.attr.direction]    = Motion.direction.CW
  pool[Motion.attr.mode]         = Motion.mode.LINEAR
  pool[Plane.attr.kind]          = Plane.kind.XY
  pool[Spindle.attr.speed]       = 0
  pool[Spindle.attr.tool]        = 0
  pool[Spindle.attr.DR]          = 0
  pool[Spindle.attr.DL]          = 0
  pool[Spindle.attr.coolant]     = Spindle.coolant.OFF
  pool[Spindle.attr.spindir]     = Spindle.spindir.CW
  pool[Registers.UNITS]          = Units.MM
  pool[Registers.WCS]            = 54
  return pool

def default():
  return construct(Motion, StateDict())