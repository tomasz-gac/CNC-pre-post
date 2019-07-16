from enum import IntEnum, unique
  
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
class Cartesian(IntEnum):
  # ABSOLUTE
  X = 14
  Y = 15
  Z = 16
  # INCREMENTAL
  XINC   = 17
  YINC   = 18
  ZINC   = 19
  
@unique
class Polar(IntEnum):
  # ABSOLUTE
  ANG = 20
  RAD = 21
  LEN = 23
  # INCREMENTAL
  ANGINC = 24
  RADINC = 25
  LENINC = 26
  
@unique
class Angular(IntEnum):
  # ABSOLUTE
  A = 27
  B = 28
  C = 29
  # INCREMENTAL
  AINC   = 30
  BINC   = 31
  CINC   = 32

@unique
class Center(IntEnum): # CIRCLE CENTER X Y Z
  X = 33
  Y = 34
  Z = 35
  XINC  = 36
  YINC  = 37
  ZINC  = 38
  
absolute    = [ Cartesian.X, Cartesian.Y, Cartesian.Z, 
                Polar.ANG, Polar.RAD, Polar.LEN,
                Angular.A, Angular.B, Angular.C, 
                Center.X, Center.Y, Center.Z ]

incremental = [ Cartesian.XINC, Cartesian.YINC, Cartesian.ZINC, 
                Polar.ANGINC, Polar.RADINC, Polar.LENINC,
                Angular.AINC, Angular.BINC, Angular.CINC, 
                Center.XINC, Center.YINC, Center.ZINC ]

abs2inc = { 
  Cartesian.X : Cartesian.XINC, Cartesian.Y : Cartesian.YINC, Cartesian.Z : Cartesian.ZINC, 
  Polar.ANG : Polar.ANGINC, Polar.RAD : Polar.RADINC, Polar.LEN : Polar.LENINC,
  Angular.A : Angular.AINC, Angular.B : Angular.BINC, Angular.C : Angular.CINC, 
  Center.X : Center.XINC, Center.Y : Center.YINC, Center.Z : Center.ZINC
}

inc2abs = { value : key for key, value in abs2inc.items() }
 
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
  result.update( { key : 0 for key in list(Polar) } )
  result.update( { key : 0 for key in list(Angular) } )
  result.update( { key : 0 for key in list(Center) } )
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
  def __init__( self, kind = Cartesian ):
    self.kind = kind
  def __call__( self, state ):
      # find all absolute coordinates that match 'self.kind'
      # that are missing from state.symtable
      # and set their incremental counterparts to 0
    constants = { abs2inc[abs] : 0
      for abs in absolute
        if abs not in state.symtable and
           abs in self.kind
      }
      # In case the user specified incremental coordinates,
      # update constants with symtable to override conflicts
    constants.update( state.symtable )
    state.symtable = constants
    
