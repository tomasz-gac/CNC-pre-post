import re

from babel.terminal import *
from babel import State
import babel.rule       as r
import babel.compiler   as c

import languages.heidenhain.commands as cmd
import languages.heidenhain.state    as s

from languages.heidenhain.state import Registers     as reg
from languages.heidenhain.state import Motion        as mot
from languages.heidenhain.state import Compensation  as comp
from languages.heidenhain.state import Direction     as dir
from languages.heidenhain.state import Coolant       as cool
from languages.heidenhain.state import Spindle       as spin

import languages.expression.parser    as expr
import babel.lang.parser as p

with open( 'languages/heidenhain/heidenhain.lang' ) as file:
  lang = p.parseStr( file.read() )
  globals().update( lang.symtable )

p = re.compile

GOTOcartesian = Lookup({ 
  p('L ')  : ( cmd.Setval(reg.MOTIONMODE, mot.LINEAR), cmd.SetGOTODefaults(s.Point), cmd.invariant ),
  p('C ')  : ( cmd.Setval(reg.MOTIONMODE, mot.CIRCULAR), cmd.SetGOTODefaults(s.Point), cmd.invariant )
}.items())

GOTOpolar = Lookup({ 
  p('LP')  : ( cmd.Setval(reg.MOTIONMODE, mot.LINEAR), cmd.SetGOTODefaults(s.Arc), cmd.invariant ),
  p('CP')  : ( cmd.Setval(reg.MOTIONMODE, mot.CIRCULAR), cmd.SetGOTODefaults(s.Arc), cmd.invariant )
}.items())

toolCallOptions = Lookup({
  p('DR\\s*[=]?')  : ( cmd.Set( reg.TOOLDR ), ),
  p('DL\\s*[=]?')  : ( cmd.Set( reg.TOOLDL ), ),
  p('S')           : ( cmd.Set( reg.SPINSPEED ), )
}.items())

def handleCoord( map ):
  def _handleCoord( match ):
    symbol = map[ match.groups()[1] ]
    if match.groups()[0] is 'I':
      return ( cmd.Set(symbol.inc), )
    else:
      return ( cmd.Set(symbol.abs), )
    
  return _handleCoord
  
cartesianCoordMap = { 
  'X' : s.Point.X.attr, 
  'Y' : s.Point.Y.attr, 
  'Z' : s.Point.Z.attr, 
  'A' : s.Angular.A.attr, 
  'B' : s.Angular.B.attr, 
  'C' : s.Angular.C.attr
}

cartesianCoord = Switch({
  p(pattern) : handleCoord(cartesianCoordMap) for pattern in
  [ "(I)?(X)", "(I)?(Y)", "(I)?(Z)", 
    "(I)?(A)", "(I)?(B)", "(I)?(C)"]
}.items())

polarCoordMap = { 
  'PA' : s.Arc.ANG.attr, 
  'PR' : s.Arc.RAD.attr,
  'X'  : s.Arc.LEN.attr, 
  'Y'  : s.Arc.LEN.attr, 
  'Z'  : s.Arc.LEN.attr
}

polarCoord = Switch({
  p('(I)?(PA)')    : handleCoord(polarCoordMap),
  p('(I)?(PR)')    : handleCoord(polarCoordMap),
  p('(I)?(X|Y|Z)') : handleCoord(polarCoordMap),
}.items())

CCcoordmap = { 
  'X' : s.Origin.OX.attr, 
  'Y' : s.Origin.OY.attr, 
  'Z' : s.Origin.OZ.attr
}

CCcoord = Switch({
  p(pattern) : handleCoord(CCcoordmap) for pattern in
  [ "(I)?(X)", "(I)?(Y)", "(I)?(Z)" ]
}.items())
  
compensation = Lookup( { 
  p('R0') : ( cmd.Setval(reg.COMPENSATION, comp.NONE), ),
  p('RL') : ( cmd.Setval(reg.COMPENSATION, comp.LEFT), ),
  p('RR') : ( cmd.Setval(reg.COMPENSATION, comp.RIGHT), )
}.items())

direction = Lookup( { 
  p('DR[-]') : ( cmd.Setval(reg.DIRECTION, dir.CW), ),
  p('DR[+]') : ( cmd.Setval(reg.DIRECTION, dir.CCW), )
}.items())

def handleAux( match ):
  aux = int(match.groups()[0])
  command = { 
    0  : ( cmd.stop, ), 
    1  : ( cmd.optionalStop, ), 
    3  : ( cmd.Setval(reg.SPINDIR, spin.CW), ),
    4  : ( cmd.Setval(reg.SPINDIR, spin.CCW), ),
    5  : ( cmd.Setval(reg.SPINDIR, spin.OFF), ),
    6  : ( cmd.toolchange, ), 
    8  : ( cmd.Setval(reg.COOLANT, cool.FLOOD), ),
    9  : ( cmd.Setval(reg.COOLANT, cool.OFF), ),
    30 : ( cmd.end, ),
    91 : ( cmd.Temporary(reg.WCS), cmd.Setval(reg.WCS, 0) )
  }
  try:
    return command[aux]
  except KeyError:
    raise RuntimeError('Unknown auxillary function M'+str(aux) )

terminals = {
  'XYZABC'            : cartesianCoord,
  'PAPRL'             : polarCoord,
  'CCXYZ'             : CCcoord,
  'lineno'            : Wrapper( expr.number , lambda x : ( cmd.Setval(reg.LINENO, x[0]), ) ),
  'F'                 : Return( cmd.Set(reg.FEED) ).If(p('F')),
  'MAX'               : Return( Push(-1) ).If(p('MAX')),
  'compensation'      : compensation,
  'direction'         : direction,
  'LC'                : GOTOcartesian,
  'LPCP'              : GOTOpolar,
  'MOVE'              : Return( cmd.invariant ),
  'UPDATE'            : Return( cmd.invariant ),
  'CC'                : Return( cmd.invariant ).If(p('CC')),
  'auxilary'          : If(p('M(\\d+)'), handleAux),
  'begin_pgm'         : Return().If(p('BEGIN PGM (.+) (MM|INCH)')),
  'end_pgm'           : Return().If(p('END PGM (.+)')),
  'comment'           : Return().If(p('[;][ ]*(.*)')),
  'blockFormStart'    : Return(cmd.discard).If(p('BLK FORM 0\\.1 (X|Y|Z)')),
  'blockFormEnd'      : Return(cmd.discard).If(p('BLK FORM 0\\.2')),
  'fn_f'              : Return(cmd.invariant).If(p('FN 0\\:')),
  'tool_call'         : Return(cmd.Set(reg.TOOLNO), cmd.invariant, cmd.toolchange ).If(p('TOOL CALL')),
  'tool_axis'         : Return().If(p('(X|Y|Z)')),
  'tool_options'      : toolCallOptions,
  'primary'           : expr.primary,
  'number'            : expr.number,
  'expression'        : expr.Parse
}

# terminals = pushTerminals( terminals )

Parse = heidenhain.compile( c.Reordering( terminals ) )

      
def bench( n = 1000 ):
  import time
  start = time.time()
  q = None
  r = None
  for i in range(n):
    q = State( 'L X+50 Y-30 Z+150 R0 FMAX' )
    r = Parse( q )
  print( time.time() - start )
  print(q.symtable)
  print(r)
  