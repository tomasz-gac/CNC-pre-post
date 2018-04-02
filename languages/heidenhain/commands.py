from enum import IntEnum, unique

@unique
class Commands(IntEnum):
  SET = 9         # UPDATE STATE ASSUMING INVARIANTS
  STOP = 10       # PROGRAM STOP
  OPTSTOP = 11    # PROGRAM OPTIONAL STOP
  TOOLCHANGE = 12 # CHANGE TOOL TO Registers.TOOLNO

@unique
class Registers(IntEnum):
  # CURRENT X Y Z A B C
  X = 0
  Y = 1
  Z = 2
  A = 3
  B = 4
  C = 5
  # CURRENT ANGLE AND RADIUS RELATIVE TO CC
  ANG = 6
  RAD = 7
  # CIRCLE CENTER X Y Z
  CX = 8
  CY = 9
  CZ = 10
  # INCREMENTAL VALUES FOR X Y Z A B C CX CY CZ ANG RAD
  XINC   = 11
  YINC   = 12
  ZINC   = 13
  AINC   = 14
  BINC   = 15
  CINC   = 16
  CXINC  = 17
  CYINC  = 18
  CZINC  = 19
  ANGINC = 20
  RADINC = 21
  COMPENSATION = 22  # COMPENSATION TYPE
  DIRECTION    = 23  # CIRCLE DIRECTION
  LINENO       = 24  # LINE NUMBER
  UNITS        = 25  # MACHINE UNITS
  FEED         = 26  # MACHINE FEED
  SPINSPEED    = 27  # SPINDLE SPEED
  MOTIONMODE   = 28  # POSITIONING MOTION MODE
  TOOLNO       = 29  # TOOL NUMBER
  TOOLDL       = 30  # TOOL DELTA LENGTH
  TOOLDR       = 31  # TOOL DELTA RADIUS
  

incmap = { 
  Registers.X : Registers.XINC, Registers.Y : Registers.YINC, Registers.Z : Registers.ZINC, 
  Registers.A : Registers.AINC, Registers.B : Registers.BINC, Registers.C : Registers.CINC, 
  Registers.ANG : Registers.ANGINC, Registers.RAD : Registers.RADINC,
  Registers.CX : Registers.CXINC, Registers.CY : Registers.CYINC, Registers.CZ : Registers.CZINC
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