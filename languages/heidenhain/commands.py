from enum import IntEnum, unique

@unique
class Commands(IntEnum):
  UPDATE  = 8     # UPDATE REGISTERS
  MOVE    = 9     # UPDATE AND MOVE TO POSITION ASSUMING COORDINATE INVARIANTS
  DISCARD = 10    # DISCARD STATE BUFFER
  TMP     = 11    # SET REGISTER VALUE AS TEMPORARY AND RESTORE IT AFTER UPDATE
  STOP    = 12    # PROGRAM STOP
  OPTSTOP = 13    # PROGRAM OPTIONAL STOP
  TOOLCHANGE = 14 # CHANGE TOOL TO Registers.TOOLNO
  
@unique
class Position(IntEnum):
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
  # INCREMENTAL VALUES FOR X Y Z A B C CX CY CZ ANG RAD
  XINC   = 8
  YINC   = 9
  ZINC   = 10
  AINC   = 11
  BINC   = 12
  CINC   = 13
  ANGINC = 14
  RADINC = 15
 
@unique
class Registers(IntEnum):
  # CIRCLE CENTER X Y Z
  CX = 16
  CY = 17
  CZ = 18
  CXINC  = 19
  CYINC  = 20
  CZINC  = 21
  COMPENSATION = 22  # COMPENSATION TYPE
  DIRECTION    = 23  # CIRCLE DIRECTION
  LINENO       = 24  # LINE NUMBER
  UNITS        = 25  # MACHINE UNITS
  FEED         = 26  # MACHINE FEED
  SPINSPEED    = 27  # SPINDLE SPEED
  SPINDIR      = 28  # SPINDLE ROTATION DIRECTION
  MOTIONMODE   = 29  # POSITIONING MOTION MODE
  TOOLNO       = 30  # TOOL NUMBER
  TOOLDL       = 31  # TOOL DELTA LENGTH
  TOOLDR       = 32  # TOOL DELTA RADIUS
  COOLANT      = 33  # COOLANT TYPE
  WCS          = 34  # WORLD COORDINATE SYSTEM NUMBER

incmap = { 
  Position.X : Position.XINC, Position.Y : Position.YINC, Position.Z : Position.ZINC, 
  Position.A : Position.AINC, Position.B : Position.BINC, Position.C : Position.CINC, 
  Position.ANG : Position.ANGINC, Position.RAD : Position.RADINC,
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