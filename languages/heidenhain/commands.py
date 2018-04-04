from enum import IntEnum, unique

@unique
class Commands(IntEnum):
  INVARIANT   = 8  # UPDATE STATE GIVEN INVARIANT
  UPDATE      = 9  # UPDATE STATE
  DISCARD     = 10 # DISCARD STATE BUFFER
  TMP         = 11 # SET REGISTER VALUE AS TEMPORARY AND RESTORE IT AFTER INVARIANT
  STOP        = 12 # PROGRAM STOP
  OPTSTOP     = 13 # PROGRAM OPTIONAL STOP
  TOOLCHANGE  = 14 # CHANGE TOOL TO Registers.TOOLNO
  END         = 15 # END PROGRAM

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

  
@unique
class Cartesian(IntEnum):
  # ABSOLUTE
  X = 13
  Y = 14
  Z = 15
  # INCREMENTAL
  XINC   = 16
  YINC   = 17
  ZINC   = 18
  
@unique
class Polar(IntEnum):
  # ABSOLUTE
  ANG = 19
  RAD = 20
  # INCREMENTAL
  ANGINC = 21
  RADINC = 22
  
@unique
class Angular(IntEnum):
  # ABSOLUTE
  A = 23
  B = 24
  C = 25
  # INCREMENTAL
  AINC   = 26
  BINC   = 27
  CINC   = 28

@unique
class Center(IntEnum): # CIRCLE CENTER X Y Z
  X = 29
  Y = 30
  Z = 31
  XINC  = 32
  YINC  = 33
  ZINC  = 34
  
 

incmap = { 
  Cartesian.X : Cartesian.XINC, Cartesian.Y : Cartesian.YINC, Cartesian.Z : Cartesian.ZINC, 
  Polar.ANG : Polar.ANGINC, Polar.RAD : Polar.RADINC,
  Angular.A : Angular.AINC, Angular.B : Angular.BINC, Angular.C : Angular.CINC, 
  Center.X : Center.XINC, Center.Y : Center.YINC, Center.Z : Center.ZINC
}
  
 
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