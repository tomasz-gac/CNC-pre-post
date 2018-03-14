import CNC.machine as m
import pickle
import sys
import time
import math
from os.path import basename, abspath, splitext

class OctaveOutput:
  def __init__(self):
    self.points=[]
  
  def _addPoint( self, X, Y, Z ):
    point = [ X, Y, Z ]
    if None in point: return
    self.points.append(point)
  
  def onRemark( self, value ):
    pass
  def onFeed( self, value ):
    pass
  def onCutCompensation( self, type ):
    pass
  def onSpindleSpeed( self, value ):
    pass
  def onProgramStart( self, name, units ):
    pass
  def onProgramEnd( self ):
    pass
  def onBlockFormStart( self, axis, X, Y, Z ):
    pass
  def onBlockFormEnd( self, X, Y, Z ):
    pass
  def onLinear( self, startX, startY, startZ, endX, endY, endZ ):
    self._addPoint(endX, endY, endZ)
  def onCircleCenter( self, startCCX, startCCY, startCCZ, endCCX, endCCY, endCCZ ):
    pass
  def onCircular( self, sX, sY, sZ, eX, eY, eZ, CCX, CCY, CCZ ):
    self._addPoint(eX, eY, eZ)
  def onToolCall( self, machine, command ):
    pass
  def onAuxilaryFunction( self, machine, command ):
    pass

class Check:
  def __init__(self):
    self.log=[]
    self.zLevel = None;
    self.lineNumber = None
  
  def onLineNumber( self, n ):
    self.lineNumber = n
  def onRemark( self, value ):
    pass
  def onFeed( self, value ):
    pass
  def onCutCompensation( self, type ):
    pass
  def onSpindleSpeed( self, value ):
    pass
  def onProgramStart( self, name, units ):
    pass
  def onProgramEnd( self ):
    pass
  def onBlockFormStart( self, axis, X, Y, Z ):
    pass
  def onBlockFormEnd( self, X, Y, Z ):
    pass
  def onLinear( self, startX, startY, startZ, endX, endY, endZ, feed, rapid ):
    if( not rapid ): return
    if startZ is None or endZ is None: return
    if self.zLevel is None:
      if startZ > 0 and endZ > 0:
        if startX != endX or startY != endY:
          self.zLevel = startZ if startZ > endZ else endZ
          self.log.append("Ustawienie wysokości bezpiecznej na " + str(self.zLevel) + "\n")
      return
    if( startX != endX or startY != endY ):
      printPos = False
      log = []
      if( startZ != endZ ):
        log.append("BŁĄD : Ruch pozycjonujący w trzech osiach.")
      if( endZ < 0 ):
        log.append("BŁĄD : Ruch pozycjonujący poniżej Z=0.")
      elif( endZ < self.zLevel ):
        log.append("OSTRZEŻENIE : Ruch pozycjonujący poniżej wysokości bezpiecznej.")
      
      if( len(log) > 0):
        self.log.append( str(self.lineNumber) + ' : ('
                         + str(startX) + ", " + str(startY) + ", " + str(startZ) + 
                         ") -> (" + str(endX) + ", " + str(endY) + ", " + str(endZ) + ")" )
        self.log += log
        self.log.append("\n")
      
      
  def onCircleCenter( self, startCCX, startCCY, startCCZ, endCCX, endCCY, endCCZ ):
    pass
  def onCircular( self, sX, sY, sZ, eX, eY, eZ, CCX, CCY, CCZ, feed, rapid ):
    pass
  def onToolCall( self, machine, command ):
    pass
  def onAuxilaryFunction( self, machine, command ):
    pass
  def onCoordinateChange( self, number, modal ):
    pass
 
    
machine = m.Machine(Check())

def execute( parser, machine, commands ):
  for command in commands:
    parser.lexer.set(command)
    cmd, success = parser.parse()
    if success:
      machine.accept( cmd )
    else:
      raise RuntimeError('Invalid command : '+str(cmd))
    
if len(sys.argv) > 1:
  fname = splitext(basename(sys.argv[1]))[0]+".p"
  with open( fname, 'rb' ) as ast:
    program = pickle.load( ast )    
  for line in program:
      machine.accept(line)
  with open( sys.argv[1]+'.txt', 'w' ) as f:
    for line in machine.callback.log:
      f.write( line + "\n" )
