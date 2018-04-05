import generator.terminal as t
import generator.rule     as r
import generator.compiler as c

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
  GOTOtokensCartesian.linear    : [ mot.LINEAR,    reg.MOTIONMODE, art.SET, cmd.INVARIANT ],
  GOTOtokensCartesian.circular  : [ mot.CIRCULAR,  reg.MOTIONMODE, art.SET, cmd.INVARIANT ],
  GOTOtokensPolar.linear        : [ mot.LINEAR,    reg.MOTIONMODE, art.SET, cmd.INVARIANT ],
  GOTOtokensPolar.circular      : [ mot.CIRCULAR,  reg.MOTIONMODE, art.SET, cmd.INVARIANT ]
})

  
@unique
class ToolCallTokens(Enum):
  DR = 'DR\\s*[=]?'
  DL = 'DL\\s*[=]?'
  S  = 'S'

toolOptLookup = t.make_lookup({
  ToolCallTokens.DR : [ reg.TOOLDR,    art.SET ],
  ToolCallTokens.DL : [ reg.TOOLDL,    art.SET ],
  ToolCallTokens.S  : [ reg.SPINSPEED, art.SET ]
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
  PA = "(I)?(PA)"
  PR = "(I)?(PR)"

coordmap = { 
  CartCoordinateTokens.X : cart.X, CartCoordinateTokens.Y : cart.Y, CartCoordinateTokens.Z : cart.Z, 
  CartCoordinateTokens.A : ang.A, CartCoordinateTokens.B : ang.B, CartCoordinateTokens.C : ang.C, 
  PolarCoordinateTokens.PA : pol.ANG, PolarCoordinateTokens.PR : pol.RAD 
}

CCcoordmap = { 
 CartCoordinateTokens.X : cen.X, CartCoordinateTokens.Y : cen.Y, CartCoordinateTokens.Z : cen.Z
}


def handleCoord( map ):
  def _handleCoord( token ):
    token = token[0]
    symbol = map[token.type]
    if token.groups[0] is 'I':
      symbol = commands.incmap[symbol]
    return [ symbol, art.SET ]
  return _handleCoord

@unique
class Compensation(Enum):
  R0 = 'R0'
  RR = 'RR'
  RL = 'RL'  
  
compensationLookup = t.make_lookup( { 
  Compensation.R0 : [ comp.NONE,  reg.COMPENSATION, art.SET ]
, Compensation.RL : [ comp.LEFT,  reg.COMPENSATION, art.SET ]
, Compensation.RR : [ comp.RIGHT, reg.COMPENSATION, art.SET ]
} )

@unique
class Direction( Enum ):
  CW = 'DR[-]'
  CCW = 'DR[+]'

directionLookup = t.make_lookup( { 
  Direction.CW  : [ dir.CW,   reg.DIRECTION, art.SET ]
, Direction.CCW : [ dir.CCW,  reg.DIRECTION, art.SET ]
} )

def handleAux( result ):
  aux = int(result[0].groups[0])
  command = { 
    0  : [ cmd.STOP ], 
    1  : [ cmd.OPTSTOP ], 
    3  : [ spin.CW,  reg.SPINDIR, art.SET ],
    4  : [ spin.CCW, reg.SPINDIR, art.SET ],
    5  : [ spin.OFF, reg.SPINDIR, art.SET ],
    6  : [ cmd.TOOLCHANGE ], 
    8  : [ cool.FLOOD, reg.COOLANT, art.SET ],
    9  : [ cool.OFF,   reg.COOLANT, art.SET ],
    30 : [ cmd.END ],
    91 : [ reg.WCS, cmd.TMP, 0, reg.WCS, art.SET ]
  }
  try:
    return command[aux]
  except KeyError:
    raise RuntimeError('Unknown auxillary function M'+str(aux) )
    
  


terminals = t.make({
  'XYZABC'            : t.make( CartCoordinateTokens ) >> handleCoord( coordmap ),
  'PAPR'              : t.make( PolarCoordinateTokens ) >> handleCoord( coordmap ),
  'CCXYZ'             : t.make( CartCoordinateTokens ) >> handleCoord( CCcoordmap ),
  'lineno'            : expr.number >> (lambda x : [ x[0], reg.LINENO, art.SET ]),
  'F'                 : t.make('F').ignore( [ reg.FEED, art.SET ] ),
  'MAX'               : t.make('MAX').ignore( [ -1 ] ),
  'compensation'      : compensationLookup(Compensation),
  'direction'         : directionLookup( Direction ),
  'L/C'               : cmdLookup(GOTOtokensCartesian),
  'LP/CP'             : cmdLookup(GOTOtokensPolar),
  'MOVE'              : t.Return( [ cmd.INVARIANT ] ),
  'UPDATE'            : t.Return( [ cmd.UPDATE ] ),
  'CC'                : t.make('CC').ignore( [cmd.UPDATE] ),
  'auxilary'          : t.make( 'M(\\d+)' ) >> handleAux,
  'begin_pgm'         : t.make('BEGIN PGM (.+) (MM|INCH)').ignore(),
  'end_pgm'           : t.make('END PGM (.+)').ignore(),
  'comment'           : t.make('[;][ ]*(.*)').ignore(),
  'block form start'  : t.make('BLK FORM 0\\.1 (X|Y|Z)').ignore( [cmd.DISCARD] ),
  'block form end'    : t.make('BLK FORM 0\\.2').ignore( [cmd.DISCARD] ),
  'fn_f'              : t.make('FN 0\\:').ignore([cmd.UPDATE]),
  'tool call'         : t.make('TOOL CALL').ignore( [reg.TOOLNO, art.SET, cmd.UPDATE, cmd.TOOLCHANGE] ),
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
  