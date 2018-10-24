import copy
import math

import languages.heidenhain.commands as cmd
import babel.state as s

def angNorm( a ):
  return (a+2*math.pi) % (2 * math.pi)
def movePolar( start1, start2, center1, center2, A, AINC, R, RINC ):
  r1, r2 = (start1 - center1), (start2 - center2)
  targetA = A*math.pi/180
  targetR = R            
  if AINC: targetA += angNorm(math.atan2(r2, r1))
  if RINC: targetR  += (r1*r1+r2*r2)**0.5
  
  target1 = center1 + targetR*math.cos(targetA)
  target2 = center2 + targetR*math.sin(targetA)
  return target1, target2
def getPolarPoints( plane, X, Y, Z, CCX, CCY, CCZ ):
    # returns axis coordinates and circle center coordinates depending on
    # circular motion plane to pass to movePolar
  if   plane is cmd.Plane.YZ:  #YZ plane
    return Y, Z, CCY, CCZ
  elif plane is cmd.Plane.ZX:  #ZX plane
    return Z, X, CCZ, CCX
  elif plane is cmd.Plane.XY:  #XY plane
    return X, Y, CCX, CCY
    
class State:
  def __init__( self ):
    self.lineNumber = 0
    self.units = None
    self.name = None
    self.axis = None
    self.blockStart = None
    self.blockEnd = None
    self.X = None
    self.Y = None
    self.Z = None
    self.A = None
    self.B = None
    self.C = None
    self.compensation = CNC.AST.Compensation.none
    self.circleCenter = None
    self.circleDirection = CNC.AST.CircleDirection.cw
    self.movementMode = CNC.AST.MovementModes.linear
    self.feed = -1
    self.spindleSpeed = 0
    self.CS = 54
    self.M = []
  def copy(self):
    return copy.copy(self)
    
class Machine:
  def __init__(self, callback):
    self.prevState  = State()
    self.state      = State()
    self.lastState = self.state.copy()
    self.coordMap = { 'X' : self.state.X, 'Y' : self.state.Y, 'Z' : self.state.Z
                    , 'A' : self.state.A, 'B' : self.state.B, 'C' : self.state.C }
    self.symtable = {}
    self._dispatch = {}
    self.callback = callback
    
  def _doMovePolar( self, command ):
      # Calculate the target coordinate value and map them to their symbols
    values = { symbol : x.value.evaluate(self.symtable) for symbol, x in command.target.items() }
    coordinates = command.target
      # get the start and center position depending on defined circle plane
    start1, start2, center1, center2 = getPolarPoints( self.state.X, self.state.Y, self.state.Z
                                                     , self.state.CCX, self.state.CCY, self.state.CCZ )
    varA = coordinates.get('A')
    varR = coordinates.get('R')
    A, AINC, R, RINC = None, None, None, None
    if varA is not None:
      A = values['A']
      AINC = varA.incremental
    else:
      A, AINC = 0, True # No angle increment
    if varR is not None:
      R = values['R']
      RINC = varR.incremental
    else:
      R, RINC = 0, True # No radius increment
       #calculate target coordinates by polar movement
    target1, target2 = movePolar( 
      start1, start2, center1, center2
    , A, AINC, R, RINC
    )
    if self.state.CCX is None:    #YZ plane
      self._setPositionAbs(Y=target1, Z=target2)
    elif self.state.CCY is None:  #ZX plane
      self._setPositionAbs(Z=target1, X=target2)
    elif self.state.CCZ is None:  #XY plane
      self._setPositionAbs(X=target1, Y=target2)
  def _getCircleCenter(self):
    CC = self.state.circleCenter
    CCX, CCY, CCZ = None, None, None
    updated = []
    if 'X' in CC:
      CCX = CC['X'].updateCartesian( self.state.X, self.symtable )
      updated.append('X')
    if 'Y' in CC:
      CCY = CC['Y'].updateCartesian( self.state.Y, self.symtable )
      updated.append('Y')
    if 'Z' in CC:
      CCZ = CC['Z'].updateCartesian( self.state.Z, self.symtable )
      updated.append('Z')
    if len(updated) < 2:
      raise RuntimeError('CircleCenter : expected 2 coordinates to form a plane')
    return CCX, CCY, CCZ  
  def accept( self, command ):
    if( type(command) not in self._dispatch ):
      method = getattr( self, type(command).__name__ )
      if( method is not None ):
        self._dispatch[type(command)] = method
      else:
        raise RuntimeError( "AST machine does not support command of type " + type(command).__name__) 
      
    return self._dispatch[ type(command) ](command)  
    
  def LineNumber( self, command ):
    self.state.lineNumber = command.number
    self.callback.onLineNumber( self.state.lineNumber )
  def Remark( self, command ):
    self.callback.onRemark( command.text )
  def SetState( self, command ):
    for key, value in command.__dict__.items():
      self.state.__dict__[key] = value
  def PushState( self, command ):
    self.prevState.__dict__[command.var] = self.state.__dict__[command.var]
  def PopState( self, command ):
    self.state.__dict__[command.var] = self.prevState.__dict__[command.var]    

  def AuxilaryFunction( self, command ):
    self.callback.onAuxilaryFunction(self, command)
  def CoordinateChange( self, command ):
    self.state.CSmodal = command.modal
    self.state.CS = command.number
    self.callback.onCoordinateChange( self.state.CS, self.state.CSmodal )
  def ExprBinary( self, command ):
    command.evaluate( self.symtable )
    
class HH:
  def __init__( self ):
    self.state = s.State('')
    self.state.symtable[cmd.Registers.POLARPLANE ] = cmd.Plane.XY
    self.state.symtable[cmd.Cartesian.X] = 0
    self.state.symtable[cmd.Cartesian.Y] = 0
    self.state.symtable[cmd.Cartesian.Z] = 0
    self.state.symtable[cmd.Center.X] = 0
    self.state.symtable[cmd.Center.Y] = 0
    self.state.symtable[cmd.Center.Z] = 0
    
  def GOTO( self, state ):
    cartesian = any( coord in state.symtable.keys() for coord in cmd.Cartesian )
    polar     = any( coord in state.symtable.keys() for coord in cmd.Polar )
    
    for symbol, inc in cmd.abs2inc.items():
      if symbol in state.symtable and inc in state.symtable:
        raise RuntimeError('Duplicate movement target coordinate specified as both absolute and incremental')
    
    if polar and cartesian:
      raise RuntimeError('Linear motion coordinates have to be either cartesian or polar')
      
    if(   state.symtable[cmd.Registers.MOTIONMODE] == cmd.Motion.LINEAR ):  
      if polar:
        self._doMovePolar( state )
      else:
        self._doMoveCartesian( state )
    if(   state.symtable[cmd.Registers.MOTIONMODE] == cmd.Motion.CIRCULAR ):
      if polar:
        self._doMovePolar( state )
      else:
        self._GOTOcircularCartesian( state, cartesian, polar )
    
  def _doMoveCartesian( self, state ):    
    coordinates = { key : value for key, value in state.symtable.items() if key in cmd.Cartesian }
    for coord in coordinates:
      if coord in cmd.absolute:
        inc = cmd.abs2inc[ coord ]
        # state.symtable[ inc ] = state.symtable[ coord ] - self.state.symtable[ coord ]
      elif coord in cmd.incremental:
        abs = cmd.inc2abs[ coord ]
        state.symtable[ abs ] = self.state.symtable[ abs ] + state.symtable[ coord ]
      else:
        raise RuntimeError('Logic error: Coordinate is neither absolute, not incremental')
    
    state.symtable = { key : value for key, value in state.symtable.items() if key not in cmd.incremental }
  
  def _doMovePolar( self, state ):
    X = self.state.symtable[cmd.Cartesian.X]
    Y = self.state.symtable[cmd.Cartesian.Y]
    Z = self.state.symtable[cmd.Cartesian.Z]
    CCX = self.state.symtable[cmd.Center.X]
    CCY = self.state.symtable[cmd.Center.Y]
    CCZ = self.state.symtable[cmd.Center.Z]
    plane = self.state.symtable[cmd.Registers.POLARPLANE ]
    start1, start2, center1, center2 = getPolarPoints( plane, X, Y, Z, CCX, CCY, CCZ )
    
    A = state.symtable.get(cmd.Polar.ANG)
    AINC = False
    if A is None: # A is incremental, or not present      
        # if no ANGINC - assume 0 increment
      A = state.symtable.get(cmd.Polar.ANGINC, 0)
      AINC = True
    
    R = state.symtable.get(cmd.Polar.RAD)
    RINC = False
    if R is None:
      R = state.symtable.get(cmd.Polar.RADINC, 0)
      RINC = True
    
    state.symtable = { key : value for key, value in state.symtable.items() if key not in cmd.Polar }
    
    #calculate target coordinates by polar movement
    target1, target2 = movePolar( 
      start1, start2, center1, center2
    , A, AINC, R, RINC
    )
    if plane is cmd.Plane.YZ:    #YZ plane
      state.symtable[ cmd.Cartesian.Y ] = target1
      state.symtable[ cmd.Cartesian.Z ] = target2
      self._doMoveCartesian( state )
    elif plane is cmd.Plane.ZX:  #ZX plane
      state.symtable[ cmd.Cartesian.Z ] = target1
      state.symtable[ cmd.Cartesian.X ] = target2
      self._doMoveCartesian( state )
    elif plane is cmd.Plane.XY:  #XY plane
      state.symtable[ cmd.Cartesian.X ] = target1
      state.symtable[ cmd.Cartesian.Y ] = target2
      self._doMoveCartesian( state )