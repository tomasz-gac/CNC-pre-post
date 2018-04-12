import re

from generator.terminal import *
from generator import State
import generator.rule       as r
import generator.compiler   as c

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

import languages.expression.commands as art

import languages.expression.parser    as expr
import languages.heidenhain.grammar   as hh

from enum import Enum, unique
from copy import deepcopy

p = re.compile

GOTOcartesian = Lookup({ 
  p('L ')  : ( mot.LINEAR,    reg.MOTIONMODE, cmd.SET, cmd.INVARIANT ),
  p('C ')  : ( mot.CIRCULAR,  reg.MOTIONMODE, cmd.SET, cmd.INVARIANT )
}.items())

GOTOpolar = Lookup({ 
  p('LP')  : ( mot.LINEAR,    reg.MOTIONMODE, cmd.SET, cmd.INVARIANT ),
  p('CP')  : ( mot.CIRCULAR,  reg.MOTIONMODE, cmd.SET, cmd.INVARIANT )
}.items())

toolCallOptions = Lookup({
  p('DR\\s*[=]?')  : ( reg.TOOLDR,    cmd.SET ),
  p('DL\\s*[=]?')  : ( reg.TOOLDL,    cmd.SET ),
  p('S')           : ( reg.SPINSPEED, cmd.SET )
}.items())

def handleCoord( map ):
  def _handleCoord( match ):
    symbol = map[ match.groups()[1] ]
    if match.groups()[0] is 'I':
      symbol = commands.incmap[symbol]
    return ( symbol, cmd.SET )
  return _handleCoord
  
coordmap = { 
  'X' : cart.X, 'Y' : cart.Y, 'Z' : cart.Z, 
  'A' : ang.A, 'B' : ang.B, 'C' : ang.C, 
  'PA' : pol.ANG, 'PR' : pol.RAD 
}

cartesianCoord = Switch({
  p(pattern) : handleCoord(coordmap) for pattern in
  [ "(I)?(X)", "(I)?(Y)", "(I)?(Z)", 
    "(I)?(A)", "(I)?(B)", "(I)?(C)"]
}.items())

polarCoord = Switch({
  p('(I)?(PA)') : handleCoord(coordmap),
  p('(I)?(PR)') : handleCoord(coordmap)
}.items())

CCcoordmap = { 'X' : cen.X, 'Y' : cen.Y, 'Z' : cen.Z }

CCcoord = Switch({
  p(pattern) : handleCoord(CCcoordmap) for pattern in
  [ "(I)?(X)", "(I)?(Y)", "(I)?(Z)" ]
}.items())
  
compensation = Lookup( { 
  p('R0') : ( comp.NONE,  reg.COMPENSATION, cmd.SET ),
  p('RL') : ( comp.LEFT,  reg.COMPENSATION, cmd.SET ),
  p('RR') : ( comp.RIGHT, reg.COMPENSATION, cmd.SET )
}.items())

direction = Lookup( { 
  p('DR[-]') : ( dir.CW,   reg.DIRECTION, cmd.SET ),
  p('DR[+]') : ( dir.CCW,  reg.DIRECTION, cmd.SET )
}.items())

def handleAux( result ):
  aux = int(result[0].groups[0])
  command = { 
    0  : ( cmd.STOP ), 
    1  : ( cmd.OPTSTOP ), 
    3  : ( spin.CW,  reg.SPINDIR, cmd.SET ),
    4  : ( spin.CCW, reg.SPINDIR, cmd.SET ),
    5  : ( spin.OFF, reg.SPINDIR, cmd.SET ),
    6  : ( cmd.TOOLCHANGE ), 
    8  : ( cool.FLOOD, reg.COOLANT, cmd.SET ),
    9  : ( cool.OFF,   reg.COOLANT, cmd.SET ),
    30 : ( cmd.END ),
    91 : ( reg.WCS, cmd.TMP, 0, reg.WCS, cmd.SET )
  }
  try:
    return command[aux]
  except KeyError:
    raise RuntimeError('Unknown auxillary function M'+str(aux) )

terminals = {
  'XYZABC'            : cartesianCoord,
  'PAPR'              : polarCoord,
  'CCXYZ'             : CCcoord,
  'lineno'            : Wrapper( expr.number ,(lambda x : [ x[0], reg.LINENO, cmd.SET ]) ),
  'F'                 : Return( reg.FEED, cmd.SET ).If(p('F')),
  'MAX'               : Return( -1 ).If(p('MAX')),
  'compensation'      : compensation,
  'direction'         : direction,
  'L/C'               : GOTOcartesian,
  'LP/CP'             : GOTOpolar,
  'MOVE'              : Return( cmd.INVARIANT ),
  'UPDATE'            : Return( cmd.INVARIANT ),
  'CC'                : Return( cmd.INVARIANT ).If(p('CC')),
  'auxilary'          : If(p('M(\\d+)'), handleAux),
  'begin_pgm'         : Return().If(p('BEGIN PGM (.+) (MM|INCH)')),
  'end_pgm'           : Return().If(p('END PGM (.+)')),
  'comment'           : Return().If(p('[;][ ]*(.*)')),
  'block form start'  : Return(cmd.DISCARD).If(p('BLK FORM 0\\.1 (X|Y|Z)')),
  'block form end'    : Return(cmd.DISCARD).If(p('BLK FORM 0\\.2')),
  'fn_f'              : Return(cmd.INVARIANT).If(p('FN 0\\:')),
  'tool call'         : Return( reg.TOOLNO, cmd.SET, cmd.INVARIANT, cmd.TOOLCHANGE ).If(p('TOOL CALL')),
  'tool axis'         : Return().If(p('(X|Y|Z)')),
  'tool options'      : toolCallOptions,
  'primary'           : expr.primary,
  'number'            : expr.number,
  'expression'        : expr.Parse
}

terminals = pushTerminals( terminals )

Parse = hh.heidenhain.compile( c.Reordering( terminals ) )

      
def bench( n = 1000 ):
  import time
  start = time.time()
  q = None
  r = None
  for i in range(n):
    q = State( 'L X+50 Y-30 Z+150 R0 FMAX' )
    r = Parse( q )
  print( time.time() - start )
  print(q.stack)
  print(r)
  