import generator.terminal as t
import generator.rule     as r
import generator.injector as inj

from CNC.language import Registers as reg
import CNC.language as CNC

import expression2          as expr
import grammars.heidenhain  as hh

from enum import Enum, unique
from copy import deepcopy

@unique
class GOTOtokens(Enum):
  linear    = "L(P)?"
  circular  = "C(P)? " # does not match CC

@unique
class ToolCallTokens(Enum):
  DR = 'DR\\s*='
  DL = 'DL\\s*='
  S  = 'S'

@unique
class CoordinateTokens(Enum):
  X = "(I)?(X)"
  Y = "(I)?(Y)"
  Z = "(I)?(Z)"
  A = "(I)?(A)"
  B = "(I)?(B)"
  C = "(I)?(C)"
  PA = "(I)?(P)(A)"
  PR = "(I)?(P)(R)"
coordmap = { 'X' : reg.X, 'Y' : reg.Y, 'Z' : reg.Z, 'A' : reg.ANG, 'R' : reg.RAD }
maskmap = { reg.X : reg.XINC, reg.Y : reg.YINC, reg.Z : reg.ZINC, reg.ANG : reg.ANGINC, reg.RAD : reg.RADINC }
  
def handleCoord( token ):
  token = token[0]
  symbol = token.groups[len(token.groups)-1]
  polar = False
  incremental = False
  if len( token.groups ) == 3:
    incremental = token.groups[0] is 'I'
    polar = token.groups[1] is 'P'
    symbol = token.groups[2]
  elif len( token.groups ) == 2:
    incremental = token.groups[0] is 'I'
    symbol = token.groups[1]
  symbol = coordmap[symbol]
  inc = maskmap[symbol]
  return [ symbol, int(incremental), inc ]

@unique
class Compensation(Enum):
  R0 = 'R0'
  RR = 'RR'
  RL = 'RL'  
  
compensationLookup = t.make_lookup( { 
  Compensation.R0 : [ CNC.Compensation.NONE, reg.COMPENSATION ]
, Compensation.RL : [ CNC.Compensation.LEFT, reg.COMPENSATION ]
, Compensation.RR : [ CNC.Compensation.RIGHT, reg.COMPENSATION ]
} )

@unique
class Direction( Enum ):
  CW = 'DR[-]'
  CCW = 'DR[+]'

directionLookup = t.make_lookup( { 
  Direction.CW  : [ CNC.Direction.CW,   reg.DIRECTION ]
, Direction.CCW : [ CNC.Direction.CCW,  reg.DIRECTION ]
} )

terminals = t.make({
  'coord'             : t.make( CoordinateTokens ) >> handleCoord,
  'F'                 : t.make('F').ignore( [ reg.FEED ] ),
  'MAX'               : t.make('MAX').ignore( [ -1 ] ),
  'compensation'      : compensationLookup(Compensation),
  'direction'         : directionLookup( Direction ),
  'L/C(P)'            : GOTOtokens,
  'CC'                : 'CC',
  'M'                 : 'M',
  'begin_pgm'         : 'BEGIN PGM (.+) (MM|INCH)',
  'end_pgm'           : 'END PGM (.+)',
  'comment'           : '[;][ ]*(.*)',
  'block form start'  : 'BLK FORM 0\\.1 (X|Y|Z)',
  'block form end'    : 'BLK FORM 0\\.2',
  'fn_f'              : 'FN[ ]*(\\d+)\\:',
  'tool call'         : t.make('TOOL CALL') >> t.get(t.Task.match),
  'tool axis'         : t.make('(X|Y|Z)') >> t.get(t.Task.match),
  'tool options'      : t.make(ToolCallTokens) >> t.get(t.Task.match) ,
  'primary'           : expr.primary,
  'number'            : expr.number,
  'expression'        : expr.Parse
})

Parse = t.Parser( hh.heidenhain, terminals, inj.ReorderInjector() )

      
def bench( n = 1000 ):
  import time
  start = time.time()
  q = None
  for i in range(n):
    q = Parse('L X+50 Y-30 Z+150 R0 FMAX' )
  print( time.time() - start )
  print(q[0])
  print(q[1])
  
bench()