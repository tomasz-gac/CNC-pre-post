from enum import Enum, unique

@unique
class Commands(Enum):
  ADD   = 0,
  SUB   = 1,
  MUL   = 2,
  DIV   = 3,
  POW   = 4,
  LET   = 5,
  SETQ  = 6,
  GETQ  = 7,
  SETREG = 8,
  MOVE   = 9
  
@unique
class Registers(Enum):
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
  # CIRCLE PLANE FLAGS
  CXY = 11
  CYZ = 12
  CZX = 13
  # INCREMENTAL FLAGS FOR CX CY CZ CA CB CC CCX CCY CCZ ANG RAD
  XINC   = 14
  YINC   = 15
  ZINC   = 16
  AINC   = 17
  BINC   = 18
  CINC   = 19
  CXINC  = 20
  CYINC  = 21
  CZINC  = 22
  ANGINC = 23
  RADINC = 24
  COMPENSATION = 25  # COMPENSATION TYPE
  DIRECTION    = 26  # CIRCLE DIRECTION
  LINENO       = 27  # LINE NUMBER
  UNITS        = 28  # MACHINE UNITS
  FEED         = 29  # MACHINE FEED
  SPINSPEED    = 30  # SPINDLE SPEED
  MOTIONMODE   = 31  # POSITIONING MOTION MODE
  
@unique
class Compensation(Enum):
  NONE = 0
  LEFT = 1
  RIGHT = 2

@unique
class Direction(Enum):
  CW = 0
  CCW = 1
  
@unique
class Motion(Enum):
  LINEAR = 0
  CIRCULAR = 1