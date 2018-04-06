import generator.evaluator as ev

import languages.heidenhain.commands as commands

from languages.heidenhain.commands import Commands      as cmd
from languages.heidenhain.commands import Registers     as reg
from languages.heidenhain.commands import Cartesian     as cart
from languages.heidenhain.commands import Polar         as pol
from languages.heidenhain.commands import Angular       as ang
from languages.heidenhain.commands import Center        as cen
from languages.heidenhain.commands import Motion        as mot
from languages.heidenhain.commands import Compensation  as comp
from languages.heidenhain.commands import Direction     as dir
from languages.heidenhain.commands import Coolant       as cool
from languages.heidenhain.commands import Spindle       as spin

from languages.expression.evaluator import ArithmeticEvaluator

import copy
import math

def machine_state():
  state = { key : 0 for key in list(reg) }
  state.update( { key : 0 for key in list(cart) } )
  state.update( { key : 0 for key in list(pol) } )
  state.update( { key : 0 for key in list(ang) } )
  state.update( { key : 0 for key in list(cen) } )
  state[reg.COMPENSATION] = comp.NONE
  state[reg.DIRECTION]    = dir.CW
  state[reg.UNITS]        = commands.Units.MM
  state[reg.MOTIONMODE]   = mot.LINEAR
  state[reg.WCS]          = 54
  return state

@ev.Handler( cmd )
class CommandEvaluator:
  def __init__( self, symtable ):
    self.symtable   = symtable
    self.data       = {  }
    self.state      = machine_state()
    self.prevState  = machine_state()
    self.tmp        = {}
    
  def _restoreTMP( self ):
    self.state.update( self.tmp )
    self.tmp = {}
  
  @ev.stack2args(2)
  def SET( self, A, B ):
    try:
      table = self.data[type(B)][B] = A
    except KeyError:
      self.data[type(B)] = { B : A }
  
  def INVARIANT( self, stack ):
    self.prevState = self.state.copy()
  
  def UPDATE( self, stack ):
    self.prevState = self.state.copy()
    self.state.update( { key : value for (key, value) in self.data.items() if key in reg } )
    self.data = { 
      key : value for (key, value) in self.data.items() if key not in reg 
    }
  
  def DISCARD( self, stack ):
    self.data.clear()
    
  @ev.stack2args(1)
  def TMP( self, register ):
    self.tmp[ register ] = self.state[register]
    return []
  
  def STOP( self, stack ):
    pass
  
  def OPTSTOP( self, stack ):
    pass
  
  def TOOLCHANGE( self, stack ):
    pass
    
  def END( self, stack ):
    pass


def angNorm( a ):
  return (a+2*math.pi) % (2 * math.pi)
def movePolar( start1, start2, center1, center2, A, AINC, R, RINC ):
  r1, r2 = (start1 - center1), (start2 - center2)
  targetA = A*math.pi/180
  targetR = R            
  if AINC:  targetA += angNorm(math.atan2(r2, r1))
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

    
def _doMoveCartesian( self, command ):
  for coord in command.target.items():
      self._updateCoordinateLinear( *coord )
    
def _updateCoordinateLinear(self, symbol, coord):
    #Dispatch function for coordinate update with incremental and absolute update
  current = self.coordMap[symbol]
  if coord.incremental:
    if current is not None:
      self._setPositionInc(**{symbol : coord.value.evaluate( self.symtable )})
    else:
      raise RuntimeError('Cannot update incremental coordinate - current location unknown')
  else:
    self._setPositionAbs(**{symbol : coord.value.evaluate( self.symtable )})
def _setPositionAbs( self, X=None, Y=None, Z=None, A=None, B=None, C=None ):
  if X is not None: self.state.X = X
  if Y is not None: self.state.Y = Y
  if Z is not None: self.state.Z = Z
  if A is not None: self.state.A = A
  if B is not None: self.state.B = B
  if C is not None: self.state.C = C
def _setPositionInc( self, X=None, Y=None, Z=None, A=None, B=None, C=None ):
  if X is not None: self.state.X += X
  if Y is not None: self.state.Y += Y
  if Z is not None: self.state.Z += Z
  if A is not None: self.state.A += A
  if B is not None: self.state.B += B
  if C is not None: self.state.C += C

def _doMoveCartesian( self, command ):
  for coord in command.target.items():
      self._updateCoordinateLinear( *coord )
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
    
    
def make_machine():
  symtable = {}
  return ev.Evaluator([ 
    ArithmeticEvaluator( symtable ), 
    CommandEvaluator( symtable ) 
  ])
    
Evaluator = make_machine()



