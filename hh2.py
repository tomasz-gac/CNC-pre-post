import generator as gen
import expression2 as expr
from enum import Enum, unique

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


coordinate = ('coord' & expr.primary['sink'])['sink']
point      = coordinate & +coordinate
feed       = "F" & ( "MAX" | expr.primary )['sink']
compensation = gen.make('compensation')# gen.make( "R(L|R|0)" )
direction    = gen.make('direction') # gen.make( "DR([+]|[-])" )

gotoTail = ( ~direction & ~compensation & ~feed )['sink']
goto = 'L/C(P)' & ~point & gotoTail
circleCenter = 'CC' & point

auxilary = 'M' & expr.number['sink']

positioning = ( ( goto | circleCenter ) & (+auxilary)['sink'] )['sink']
positioningShort = ( point & gotoTail & (+auxilary)['sink'] )['sink']

begin_pgm = 'begin_pgm' # 'BEGIN PGM (.+) (MM|INCH)'
end_pgm   = 'end_pgm' # 'END PGM (.+)'
comment   = gen.make('comment') # '[;][ ]*(.*)'
BLKformStart = 'block form start' & point # 'BLK FORM 0\\.1 (X|Y|Z)'
BLKformEnd   = 'block form end' & point # 'BLK FORM 0\\.2'
fn_f         = 'fn_f' & expr.Parse # 'FN[ ]*(\\d+)\\:'

toolCall = ( 
  'tool call' & # gen.make("TOOL CALL") &
  (expr.primary & "(X|Y|Z)")['sink'] & 
  ( +( 'tool call tokens' & ( expr.primary )['sink']) )['sink'] 
  )['sink']

heidenhain = (
 ~expr.number & ( 
  positioning       |
  fn_f              |
  toolCall          |
  begin_pgm         |
  end_pgm           |
  BLKformStart      |
  BLKformEnd        |
  auxilary          |
  positioningShort
  )
& ~comment
)['sink']['source']

handlers = {
  "sink"       : gen.Sink,
  "source"     : gen.Source
}

terminals = gen.make_terminals({
  'coord'             : CoordinateTokens,
  'F'                 : 'F',
  'MAX'               : 'MAX',
  'compensation'      : 'R(L|R|0)',
  'direction'         : 'DR([+]|[-])',
  'L/C(P)'            : GOTOtokens,
  'CC'                : 'CC',
  'M'                 : 'M',
  'begin_pgm'         : 'BEGIN PGM (.+) (MM|INCH)',
  'end_pgm'           : 'END PGM (.+)',
  'comment'           : '[;][ ]*(.*)',
  'block form start'  : 'BLK FORM 0\\.1 (X|Y|Z)',
  'block form end'    : 'BLK FORM 0\\.2',
  'fn_f'              : 'FN[ ]*(\\d+)\\:',
  'tool call'         : 'TOOL CALL',
  'tool call XYZ'     : '(X|Y|Z)',
  'tool call tokens'  : ToolCallTokens
})

Parse = gen.Parser( heidenhain, terminals, handlers )
l = gen.Lexer()

def mp( grammar ):
  return gen.Parser( grammar, terminals, handlers )
  
import time
start = time.time()
for i in range(100000):
  q = Parse(l, 'L X+50 Y-30 Z+150 R0 FMAX' )
print( time.time() - start )