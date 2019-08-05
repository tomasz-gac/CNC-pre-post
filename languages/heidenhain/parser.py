import re

from babel.terminal import *
from babel import State
import babel.rule       as r
import babel.compiler   as c

import languages.heidenhain.commands as cmd

from languages.heidenhain.commands import Registers     as reg
from languages.heidenhain.commands import Motion        as mot
from languages.heidenhain.commands import Compensation  as comp
from languages.heidenhain.commands import Direction     as dir
from languages.heidenhain.commands import Coolant       as cool
from languages.heidenhain.commands import Spindle       as spin

import languages.expression.parser    as expr
import babel.lang.parser as p

with open( 'languages/heidenhain/heidenhain.lang' ) as file:
  lang = p.parseStr( file.read() )
  globals().update( lang.symtable )

p = re.compile

GOTOcartesian = Lookup({ 
  p('L ')  : ( cmd.Setval(reg.MOTIONMODE, mot.LINEAR), cmd.SetGOTODefaults(cmd.Cartesian.Absolute), cmd.invariant ),
  p('C ')  : ( cmd.Setval(reg.MOTIONMODE, mot.CIRCULAR), cmd.SetGOTODefaults(cmd.Cartesian.Absolute), cmd.invariant )
}.items())

GOTOpolar = Lookup({ 
  p('LP')  : ( cmd.Setval(reg.MOTIONMODE, mot.LINEAR), cmd.SetGOTODefaults(cmd.Polar.Absolute), cmd.invariant ),
  p('CP')  : ( cmd.Setval(reg.MOTIONMODE, mot.CIRCULAR), cmd.SetGOTODefaults(cmd.Polar.Absolute), cmd.invariant )
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
      symbol = cmd.abs2inc(symbol)
    return ( cmd.Set(symbol), )
  return _handleCoord
  
cartesianCoordMap = { 
  'X' : cmd.Cartesian.Absolute.attr.X, 
  'Y' : cmd.Cartesian.Absolute.attr.Y, 
  'Z' : cmd.Cartesian.Absolute.attr.Z, 
  'A' : cmd.Angular.Absolute.attr.A, 
  'B' : cmd.Angular.Absolute.attr.B, 
  'C' : cmd.Angular.Absolute.attr.C
}

cartesianCoord = Switch({
  p(pattern) : handleCoord(cartesianCoordMap) for pattern in
  [ "(I)?(X)", "(I)?(Y)", "(I)?(Z)", 
    "(I)?(A)", "(I)?(B)", "(I)?(C)"]
}.items())

polarCoordMap = { 
  'PA' : cmd.Polar.Absolute.attr.ANG, 
  'PR' : cmd.Polar.Absolute.attr.RAD,
  'X'  : cmd.Polar.Absolute.attr.LEN, 
  'Y'  : cmd.Polar.Absolute.attr.LEN, 
  'Z'  : cmd.Polar.Absolute.attr.LEN
}

polarCoord = Switch({
  p('(I)?(PA)')    : handleCoord(polarCoordMap),
  p('(I)?(PR)')    : handleCoord(polarCoordMap),
  p('(I)?(X|Y|Z)') : handleCoord(polarCoordMap),
}.items())

CCcoordmap = { 
  'X' : cmd.Polar.Center.Absolute.attr.X, 
  'Y' : cmd.Polar.Center.Absolute.attr.Y, 
  'Z' : cmd.Polar.Center.Absolute.attr.Z 
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
  