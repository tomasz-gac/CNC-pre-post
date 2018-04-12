import generator.terminal as t
import generator.rule     as r
import generator.compiler as c
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

import languages.expression.commands as art

import languages.expression.parser    as expr
import languages.heidenhain.grammar   as hh

from enum import Enum, unique
from copy import deepcopy

GOTOcartesian = t.Lookup({ 
  'L '  : ( mot.LINEAR,    reg.MOTIONMODE, cmd.SET, cmd.INVARIANT ),
  'C '  : ( mot.CIRCULAR,  reg.MOTIONMODE, cmd.SET, cmd.INVARIANT )
})

GOTOpolar = t.Lookup({ 
  'LP'  : ( mot.LINEAR,    reg.MOTIONMODE, cmd.SET, cmd.INVARIANT ),
  'CP'  : ( mot.CIRCULAR,  reg.MOTIONMODE, cmd.SET, cmd.INVARIANT )
})

toolCallOptions = t.Lookup({
  'DR\\s*[=]?'  : ( reg.TOOLDR,    cmd.SET ),
  'DL\\s*[=]?'  : ( reg.TOOLDL,    cmd.SET ),
  'S'           : ( reg.SPINSPEED, cmd.SET )
})

def handleCoord( map ):
  def _handleCoord( token ):
    symbol = map[ token.groups()[1] ]
    if token.groups()[0] is 'I':
      symbol = commands.incmap[symbol]
    return [ symbol, cmd.SET ]
  return _handleCoord
  
coordmap = { 
  'X' : cart.X, 'Y' : cart.Y, 'Z' : cart.Z, 
  'A' : ang.A, 'B' : ang.B, 'C' : ang.C, 
  'PA' : pol.ANG, 'PR' : pol.RAD 
}

cartesianCoord = t.Switch({
  "(I)?(X)" : handleCoord(coordmap),
  "(I)?(Y)" : handleCoord(coordmap),
  "(I)?(Z)" : handleCoord(coordmap),
  "(I)?(A)" : handleCoord(coordmap),
  "(I)?(B)" : handleCoord(coordmap),
  "(I)?(C)" : handleCoord(coordmap)
})

polarCoord = t.Switch({
  '(I)?(PA)' : handleCoord(coordmap),
  '(I)?(PR)' : handleCoord(coordmap)
})

CCcoordmap = { 
 'X' : cen.X, 'Y' : cen.Y, 'Z' : cen.Z
}

CCcoord = t.Switch({
  "(I)?(X)" : handleCoord(CCcoordmap),
  "(I)?(Y)" : handleCoord(CCcoordmap),
  "(I)?(Z)" : handleCoord(CCcoordmap)
})
  
compensation = t.Lookup( { 
  'R0' : ( comp.NONE,  reg.COMPENSATION, cmd.SET ),
  'RL' : ( comp.LEFT,  reg.COMPENSATION, cmd.SET ),
  'RR' : ( comp.RIGHT, reg.COMPENSATION, cmd.SET )
} )

direction = t.Lookup( { 
  'DR[-]' : ( dir.CW,   reg.DIRECTION, cmd.SET ),
  'DR[+]' : ( dir.CCW,  reg.DIRECTION, cmd.SET )
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
    
auxilary = t.If('M(\\d+)', handleAux)


terminals = {
  'XYZABC'            : cartesianCoord,
  'PAPR'              : polarCoord,
  'CCXYZ'             : CCcoord,
  'lineno'            : t.Wrapper( expr.number ,(lambda x : [ x[0], reg.LINENO, cmd.SET ]) ),
  'F'                 : t.If('F', t.Return( reg.FEED, cmd.SET )),
  'MAX'               : t.If('MAX', t.Return( -1 )),
  'compensation'      : compensation,
  'direction'         : direction,
  'L/C'               : GOTOcartesian,
  'LP/CP'             : GOTOpolar,
  'MOVE'              : t.Return( cmd.INVARIANT ),
  'UPDATE'            : t.Return( cmd.INVARIANT ),
  'CC'                : t.If('CC', t.Return( cmd.INVARIANT )),
  'auxilary'          : auxilary,
  'begin_pgm'         : t.If('BEGIN PGM (.+) (MM|INCH)', t.Return()),
  'end_pgm'           : t.If('END PGM (.+)', t.Return()),
  'comment'           : t.If('[;][ ]*(.*)', t.Return()),
  'block form start'  : t.If('BLK FORM 0\\.1 (X|Y|Z)', t.Return(cmd.DISCARD)),
  'block form end'    : t.If('BLK FORM 0\\.2', t.Return(cmd.DISCARD)),
  'fn_f'              : t.If('FN 0\\:', t.Return(cmd.INVARIANT)),
  'tool call'         : t.If('TOOL CALL', t.Return( reg.TOOLNO, cmd.SET, cmd.INVARIANT, cmd.TOOLCHANGE )),
  'tool axis'         : t.If('(X|Y|Z)', t.Return()),
  'tool options'      : toolCallOptions,
  'primary'           : expr.primary,
  'number'            : expr.number,
  'expression'        : expr.Parse
}

# Parse = t.StrParser( hh.heidenhain, c.Reordering( terminals ) )
Parse = hh.heidenhain.compile( c.Reordering( terminals ) )

      
def bench( n = 1000 ):
  import time
  start = time.time()
  q = None
  e = ev.Delayed( q )
  r = None
  for i in range(n):
    q = art.State( 'L X+50 Y-30 Z+150 R0 FMAX' )
    e.state = q
    r = Parse( e )
  print( time.time() - start )
  print(q.stack)
  print(r)
  