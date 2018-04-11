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

import languages.expression.commands as art

import languages.expression.parser    as expr
import languages.heidenhain.grammar   as hh

from enum import Enum, unique
from copy import deepcopy

GOTOcartesian = t.Switch({ 
  'L '  : [ mot.LINEAR,    reg.MOTIONMODE, cmd.SET, cmd.INVARIANT ],
  'C '  : [ mot.CIRCULAR,  reg.MOTIONMODE, cmd.SET, cmd.INVARIANT ]
}

GOTOpolar = t.Switch({ 
  'LP'  : [ mot.LINEAR,    reg.MOTIONMODE, cmd.SET, cmd.INVARIANT ],
  'CP'  : [ mot.CIRCULAR,  reg.MOTIONMODE, cmd.SET, cmd.INVARIANT ]
}

ToolCall = t.Switch({
  'DR\\s*[=]?'  : [ reg.TOOLDR,    cmd.SET ],
  'DL\\s*[=]?'  : [ reg.TOOLDL,    cmd.SET ],
  'S'           : [ reg.SPINSPEED,    cmd.SET ],
})

def handleCoord( map ):
  def _handleCoord( token ):
    token = token[0]
    symbol = map[token.type]
    if token.groups[0] is 'I':
      symbol = commands.incmap[symbol]
    return [ symbol, cmd.SET ]
  return _handleCoord
  
  
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

@unique
class Compensation(Enum):
  R0 = 'R0'
  RR = 'RR'
  RL = 'RL'  
  
compensationLookup = t.make_lookup( { 
  Compensation.R0 : [ comp.NONE,  reg.COMPENSATION, cmd.SET ]
, Compensation.RL : [ comp.LEFT,  reg.COMPENSATION, cmd.SET ]
, Compensation.RR : [ comp.RIGHT, reg.COMPENSATION, cmd.SET ]
} )

@unique
class Direction( Enum ):
  CW = 'DR[-]'
  CCW = 'DR[+]'

directionLookup = t.make_lookup( { 
  Direction.CW  : [ dir.CW,   reg.DIRECTION, cmd.SET ]
, Direction.CCW : [ dir.CCW,  reg.DIRECTION, cmd.SET ]
} )

def handleAux( result ):
  aux = int(result[0].groups[0])
  command = { 
    0  : [ cmd.STOP ], 
    1  : [ cmd.OPTSTOP ], 
    3  : [ spin.CW,  reg.SPINDIR, cmd.SET ],
    4  : [ spin.CCW, reg.SPINDIR, cmd.SET ],
    5  : [ spin.OFF, reg.SPINDIR, cmd.SET ],
    6  : [ cmd.TOOLCHANGE ], 
    8  : [ cool.FLOOD, reg.COOLANT, cmd.SET ],
    9  : [ cool.OFF,   reg.COOLANT, cmd.SET ],
    30 : [ cmd.END ],
    91 : [ reg.WCS, cmd.TMP, 0, reg.WCS, cmd.SET ]
  }
  try:
    return command[aux]
  except KeyError:
    raise RuntimeError('Unknown auxillary function M'+str(aux) )
    
  


terminals = t.make({
  'XYZABC'            : t.make( CartCoordinateTokens ) >> handleCoord( coordmap ),
  'PAPR'              : t.make( PolarCoordinateTokens ) >> handleCoord( coordmap ),
  'CCXYZ'             : t.make( CartCoordinateTokens ) >> handleCoord( CCcoordmap ),
  'lineno'            : expr.number >> (lambda x : [ x[0], reg.LINENO, cmd.SET ]),
  'F'                 : t.make('F').ignore( [ reg.FEED, cmd.SET ] ),
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
  'tool call'         : t.make('TOOL CALL').ignore( [reg.TOOLNO, cmd.SET, cmd.UPDATE, cmd.TOOLCHANGE] ),
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
  