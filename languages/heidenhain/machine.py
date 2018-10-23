import copy
import math

import languages.heidenhain.commands as cmd

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
def getPolarPoints( X, Y, Z, CCX, CCY, CCZ ):
    # returns axis coordinates and circle center coordinates depending on
    # circular motion plane to pass to movePolar
  if ( (CCX is None) + (CCY is None) + (CCZ is None) ) > 1:
    raise RuntimeError('Circle center is not fully defined')
  elif CCX is None:  #YZ plane
    return Y, Z, CCY, CCZ
  elif CCY is None:  #ZX plane
    return Z, X, CCZ, CCX
  elif CCZ is None:  #XY plane
    return X, Y, CCX, CCY    
  else:
    raise RuntimeError('Circle center is over-defined')
    
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
  def GOTO( self, state ):
    cartesian = any( coord in state.symtable.keys() for coord in cmd.Cartesian )
    polar     = any( coord in state.symtable.keys() for coord in cmd.Polar )
    if polar and cartesian:
      raise RuntimeError('Linear motion coordinates have to be either cartesian or polar')
      
    if(   state.symtable[cmd.Registers.MOTIONMODE == cmd.Motion.LINEAR ):  
      if polar:
        self._doMovePolar( state )    # TODO
      else:
        self._doMoveCartesian( state )
    if(   state.symtable[cmd.Registers.MOTIONMODE == cmd.Motion.CIRCULAR ):
      if polar:
        self._doMovePolar( state )      # TODO
      else:
        self._GOTOcircularCartesian( state, cartesian, polar )
    
  def _GOTOcircularCartesian(self, state ):
    pass
    '''CCX, CCY, CCZ = self._getCircleCenter()   # TODO
    
    values = { symbol : value for symbol, value in state.symtable.items() if symbol in cmd.Cartesian }
    target1 = target2 = None
    if CCX is None:  #YZ plane    
      target1 = values.get(cmd.Cartesian.Y, self.state.Y)
      target2 = values.get(cmd.Cartesian.Z, self.state.Z)
    elif CCY is None:  #ZX plane
      target1 = values.get(cmd.Cartesian.Z, self.state.Z)
      target2 = values.get(cmd.Cartesian.X, self.state.X)
    elif CCZ is None:  #XY plane
      target1 = values.get(cmd.Cartesian.X, self.state.X)
      target2 = values.get(cmd.Cartesian.Y, self.state.Y)
    else:
      raise RuntimeError('Circle center is over-defined')
    
    start1, start2, center1, center2 = getPolarPoints( self.state.X, self.state.Y, self.state.Z, CCX, CCY, CCZ )
    
    rStart  = (start1-center1)**2 + (start2-center2)**2
    rTarget  = (target1-center1)**2 + (target2-center2)**2
    if (rStart**0.5-rTarget**0.5) > 0.01:
      print("Warning : highly inaccurate radius in circular motion declaration")
    self._doMoveCartesian(state)'''
  def _doMoveCartesian( self, state ):
    for symbol, inc in cmd.incmap.items():
      if symbol in state.symtable and inc in state.symtable:
        raise RuntimeError('Duplicate movement target coordinate specified as both absolute and incremental')
    
    coordinates = { key : value for key, value in state.symtable if key in cmd.Cartesian or key in cmd.Polar or key in cmd.Angular }
    for coord in coordinates:
      if coord in cmd.absolute:
        inc = cmd.abs2inc[ coord ]
        state.symtable[ inc ] = state.symtable[ coord ] - self.state.symtable[ coord ]
      elif coord in cmd.incremental:
        abs = cmd.inc2abs[ coord ]
        state.symtable[ abs ] = self.state.symtable[ abs ] + state.symtable[ coord ]
      else:
        raise RuntimeError('Logic error: Coordinate is neither absolute, not incremental')
  
