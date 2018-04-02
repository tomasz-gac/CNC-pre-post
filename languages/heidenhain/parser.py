import generator.terminal as t
import generator.rule     as r
import generator.compiler as c

import languages.heidenhain.commands as commands
from languages.heidenhain.commands import Registers     as reg
from languages.heidenhain.commands import Commands      as cmd
from languages.heidenhain.commands import Motion        as mot
from languages.heidenhain.commands import Compensation  as comp
from languages.heidenhain.commands import Direction     as dir
from languages.heidenhain.commands import Coolant       as cool

from languages.expression.commands import Arithmetic    as art

import languages.expression.parser    as expr
import languages.heidenhain.grammar   as hh

from enum import Enum, unique
from copy import deepcopy

@unique
class GOTOtokensCartesian(Enum):
  linear    = "L "
  circular  = "C " # whitespace does not match CC

@unique
class GOTOtokensPolar(Enum):
  linear    = "LP"
  circular  = "CP"

cmdLookup = t.make_lookup({
  GOTOtokensCartesian.linear    : [ mot.LINEAR,    reg.MOTIONMODE, art.SETREG, cmd.SET ],
  GOTOtokensCartesian.circular  : [ mot.CIRCULAR,  reg.MOTIONMODE, art.SETREG, cmd.SET ],
  GOTOtokensPolar.linear        : [ mot.LINEAR,    reg.MOTIONMODE, art.SETREG, cmd.SET ],
  GOTOtokensPolar.circular      : [ mot.CIRCULAR,  reg.MOTIONMODE, art.SETREG, cmd.SET ]
})

  
@unique
class ToolCallTokens(Enum):
  DR = 'DR\\s*='
  DL = 'DL\\s*='
  S  = 'S'

toolOptLookup = t.make_lookup({
  ToolCallTokens.DR : [ reg.TOOLDR,    art.SETREG ],
  ToolCallTokens.DL : [ reg.TOOLDL,    art.SETREG ],
  ToolCallTokens.S  : [ reg.SPINSPEED, art.SETREG ]
})
  
  
@unique
class CartCoordinateTokens(Enum):
  X = "(I)?(X)"
  Y = "(I)?(Y)"
  Z = "(I)?(Z)"
  A = "(I)?(A)"
  B = "(I)?(B)"
  C = "(I)?(C)"
  
@unique
class PolarCoordinateTokens(Enum):
  PA = "(I)?(P)(A)"
  PR = "(I)?(P)(R)"

coordmap = { 
  'X' : reg.X, 'Y' : reg.Y, 'Z' : reg.Z, 
  'A' : reg.A, 'B' : reg.B, 'C' : reg.C, 
  'R' : reg.RAD 
}

CCcoordmap = { 
  'X' : reg.CX, 'Y' : reg.CY, 'Z' : reg.CZ
}


def handleCoord( map ):
  def _handleCoord( token ):
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
    symbol = map[symbol]
    if symbol is reg.A and polar: 
      symbol = reg.ANG
    if incremental:
      symbol = commands.incmap[symbol]
    return [ symbol, art.SETREG ]
  return _handleCoord

@unique
class Compensation(Enum):
  R0 = 'R0'
  RR = 'RR'
  RL = 'RL'  
  
compensationLookup = t.make_lookup( { 
  Compensation.R0 : [ comp.NONE,  reg.COMPENSATION, art.SETREG ]
, Compensation.RL : [ comp.LEFT,  reg.COMPENSATION, art.SETREG ]
, Compensation.RR : [ comp.RIGHT, reg.COMPENSATION, art.SETREG ]
} )

@unique
class Direction( Enum ):
  CW = 'DR[-]'
  CCW = 'DR[+]'

directionLookup = t.make_lookup( { 
  Direction.CW  : [ dir.CW,   reg.DIRECTION, art.SETREG ]
, Direction.CCW : [ dir.CCW,  reg.DIRECTION, art.SETREG ]
} )

def handleAux( result ):
  aux = int(result[0].groups[0])
  command = { 
    0  : [ cmd.STOP ], 
    1  : [ cmd.OPTSTOP ], 
    3  : [ cmd.SPINCW ],
    4  : [ cmd.SPINCCW ],
    5  : [ cmd.SPINOFF ],
    6  : [ cmd.TOOLCHANGE ], 
    8  : [ cool.FLOOD ],
    9  : [ cool.OFF ],
    91 : [  ]
  }
  return command[aux]


terminals = t.make({
  'coordCartesian'    : t.make( CartCoordinateTokens ) >> handleCoord( coordmap ),
  'coordPolar'        : t.make( PolarCoordinateTokens ) >> handleCoord( coordmap ),
  'coordCC'           : t.make( CartCoordinateTokens ) >> handleCoord( CCcoordmap ),
  'lineno'            : expr.number >> (lambda x : [ x[0], reg.LINENO, art.SETREG ]),
  'F'                 : t.make('F').ignore( [ reg.FEED, art.SETREG ] ),
  'MAX'               : t.make('MAX').ignore( [ -1 ] ),
  'compensation'      : compensationLookup(Compensation),
  'direction'         : directionLookup( Direction ),
  'L/C'               : cmdLookup(GOTOtokensCartesian),
  'LP/CP'             : cmdLookup(GOTOtokensPolar),
  'set'               : t.Return( [cmd.SET] ),
  'CC'                : t.make('CC').ignore( [cmd.SET] ),
  'auxilary'          : t.make( 'M(\\d+)' ) >> handleAux,
  'begin_pgm'         : t.make('BEGIN PGM (.+) (MM|INCH)').ignore(),
  'end_pgm'           : t.make('END PGM (.+)').ignore(),
  'comment'           : t.make('[;][ ]*(.*)').ignore(),
  'block form start'  : t.make('BLK FORM 0\\.1 (X|Y|Z)').ignore( [cmd.IGNORE] ),
  'block form end'    : t.make('BLK FORM 0\\.2').ignore( [cmd.IGNORE] ),
  'fn_f'              : t.make('FN 0\\:').ignore(),
  'tool call'         : t.make('TOOL CALL').ignore( [reg.TOOLNO, art.SETREG, cmd.SET] ),
  'tool axis'         : t.make('(X|Y|Z)').ignore(),
  'tool options'      : toolOptLookup(ToolCallTokens),
  'primary'           : expr.primary,
  'number'            : expr.number,
  'expression'        : expr.Parse
})

Parse = t.StrParser( hh.heidenhain, c.Reordering( terminals ) )

      
def bench( n = 1000 ):
  import time
  start = time.time()
  q = None
  for i in range(n):
    q = Parse( 'L X+50 Y-30 Z+150 R0 FMAX' )
  print( time.time() - start )
  print(q[0])
  print(q[1])
  