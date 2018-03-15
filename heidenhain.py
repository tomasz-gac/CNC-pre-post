import generator as gen
import expression2 as expr
import CNC
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

def handleCoordinate( data ):
  token, value = tuple(data)
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
  return { symbol : CNC.AST.Coordinate( value, incremental, polar ) }

def handlePoint( axes ):
  coordinates = {}
  coordinates.update( axes[0] )
  lst = list(axes[1])
  for coordinate in lst:
    if coordinate.keys() <= coordinates.keys():
      raise RuntimeError('Duplicate coordinate in point declaration')
    else:
      coordinates.update( coordinate )
  return coordinates
  
def handleFeed( feed ):
  token = feed[1]
  if isinstance(token,gen.Task):  # rapid feed
    token = None
  s = CNC.AST.SetState()
  s.feed = token
  return s

_comptable = { 
  '0' : CNC.AST.Compensation.none
, 'L' : CNC.AST.Compensation.left
, 'R' : CNC.AST.Compensation.right
}
  
def handleCompensation( comp ):  
  s = CNC.AST.SetState()
  s.compensation = _comptable.get( comp.groups[0], None )
  return s

_dirtable = {'-' : CNC.AST.CircleDirection.cw, '+' : CNC.AST.CircleDirection.ccw }
  
def handleDirection( direction ):
  s = CNC.AST.SetState()
  s.circleDirection = _dirtable.get( direction.groups[0], None )
  return s

_movtable = { 
  GOTOtokens.linear   : CNC.AST.MovementModes.linear 
, GOTOtokens.circular : CNC.AST.MovementModes.circular
}

def _checkPointCartesian( coordinates, n=None ):
  angular = [ x in ['A', 'B', 'C'] for x in coordinates.keys() ]
  if any(angular):
    raise RuntimeError('Expected cartesian coordinates')
  if n is not None and len(coordinates) > n:
    raise RuntimeError('Expected exactly ' + str(n) + ' cartesian coordinates')
    
def _checkPointPolar( coordinates ):
  if not all( [ x.polar for x in coordinates.values() ] ):
    raise RuntimeError('Expected polar coordinates')
  if len( coordinates ) > 2:
    raise RuntimeError('Expected at most two polar coordinates')

def handleGoto( lst ):
  if not any( lst ):
    return gen.ParserFailed
  state = CNC.AST.SetState()
  result = []
  
  movementModeToken   = lst[0]
  movementMode        = None
  coordinates         = lst[1]
  direction           = lst[2]  
  
  polar = False
  if movementModeToken is not None:
    movementMode = _movtable[ movementModeToken.type ]
    polar = movementModeToken.groups[0] is not None
  if direction is not None:
    if movementMode is CNC.AST.MovementModes.linear:
      raise RuntimeError("Direction declaration is only vaid for circular motion positioning statements")
    movementMode = CNC.AST.MovementModes.circular
  
  if movementMode is not None:
    state.movementMode = movementMode
  if coordinates is not None:
    if polar:
      _checkPointPolar( coordinates )    
    result.append( CNC.AST.GOTO(coordinates, polar) )  
    
  state.merge( ( x for x in lst if isinstance(x, CNC.AST.SetState) ) )
  if( len(state.__dict__) > 0):
    result.insert( 0, state )
  
  if hasattr( state, "feed" ) and state.feed is None: # rapid feed
    state.feed = CNC.AST.ExprTerminal(-1)
    result.insert( 0, CNC.AST.PushState("feed") )
    result.append( CNC.AST.PopState("feed") )
  
  return result

def handleCircleCenter( lst ):
  _checkPointCartesian( lst[1], 2 )
  state = CNC.AST.SetState()
  state.circleCenter = lst[1]
  return [state]

def handleToolCall( lst ):
  toolOptions = CNC.AST.SetState()
  toolOptions.toolNumber        = lst[1]
  toolOptions.toolAxis          = lst[2].groups[0]
  if lst[3] is not None:
    toolOptions.spindleSpeed    = list(lst[3])[1]
  if lst[4] is not None:
    toolOptions.toolDeltaRadius = list(lst[4])[1]
  if lst[5] is not None:
    toolOptions.toolDeltaLength = list(lst[5])[1]
  return [toolOptions]
  
def handleBegin( token ):
  state = CNC.AST.SetState()
  state.name = token.groups[0]
  state.units = token.groups[1]
  return [state]

def handleEnd( token ):
  state = CNC.AST.SetState()
  state.name = token.groups[0]
  return [state]
  
def handleComment( token ):
  return [CNC.AST.Remark( token.groups[0] )]

def handleBLKformStart( lst ):
  blkInfo = CNC.AST.SetState()
  blkInfo.materialAxis    = lst[0].groups[0]
  blkInfo.materialBegin   = lst[1]
  if len(blkInfo.materialBegin) != 3:
    raise RuntimeError('Expected a 3 coordinate point declaration')
  if any([x.polar or x.incremental for x in blkInfo.materialBegin.values()]):
    raise RuntimeError('Expected unqualified point coordinates')
  _checkPointCartesian( blkInfo.materialBegin, 3 )
  return [blkInfo]

def handleBLKformEnd( lst ):
  blkInfo = CNC.AST.SetState()
  blkInfo.materialEnd  = lst[1]
  if len(blkInfo.materialEnd) != 3:
    raise RuntimeError('Expected a 3 coordinate point declaration')
  if any([x.polar or x.incremental for x in blkInfo.materialEnd.values()]):
    raise RuntimeError('Expected unqualified point coordinates')
  _checkPointCartesian( blkInfo.materialEnd, 3 )
  return [blkInfo]

def handleFn_f( lst ):
  token = lst[0]
  if token.groups[0] == '0':
    return [lst[1]]
  else:
    raise RuntimeError( 'Unknown FN function: '+token.groups[0] )
  
def handleAuxilary( lst ):
  # if m == 91:
  #  return CNC.AST.CoordinateChange( 0 )
  return CNC.AST.AuxilaryFunction( lst[1] )

def handlePositioning( lst ):
  result = list( lst[0] )
  if lst[1] is not None:
    result = list(lst[1]) + result
  return result
  
coordinate = CoordinateTokens & expr.primary
point      = coordinate & +coordinate
feed       = gen.Ignore("F") & ( "MAX" | expr.primary )
compensation = gen.make( "R(L|R|0)" )
direction    = gen.make( "DR([+]|[-])" )

goto = gen.Push( ~gen.make(GOTOtokens) & gen.Push( ~point ) & gen.Push( ~direction & [ ~compensation, ~feed ] ) )
circleCenter = gen.make("CC") & point

auxilary = gen.Ignore("M") & expr.number

positioning = ( goto | circleCenter ) & +auxilary

begin_pgm = gen.make('BEGIN PGM (.+) (MM|INCH)')
end_pgm   = gen.make('END PGM (.+)')
comment   = gen.make('[;][ ]*(.*)')
BLKformStart = gen.make( "BLK FORM 0\\.1 (X|Y|Z)" ) & point
BLKformEnd   = gen.Ignore( "BLK FORM 0\\.2" )       & point
fn_f         = gen.make('FN[ ]*(\\d+)\\:')          & expr.Parse

toolCall = gen.Ignore("TOOL CALL") & [ 
  expr.primary, "(X|Y|Z)"
, ~( gen.Ignore("S") & expr.primary )
, ~( gen.Ignore("DR") & expr.primary )
, ~( gen.Ignore("DL") & expr.primary ) 
]

heidenhain = (
~ gen.Ignore(expr.number)
& ( positioning | [
      fn_f
    , toolCall
    , begin_pgm 
    , end_pgm 
    , BLKformStart 
    , BLKformEnd
    , auxilary
    ]
  )
& ~comment
)

_unpack = lambda x : list( (y for y in gen.rule._flatten(x) if y is not None) )

handlers = { 
  coordinate    : handleCoordinate 
, point         : handlePoint
, feed          : handleFeed
, compensation  : handleCompensation
, direction     : handleDirection
, goto          : handleGoto
, circleCenter  : handleCircleCenter
, toolCall      : handleToolCall
, begin_pgm     : handleBegin
, end_pgm       : handleEnd
, comment       : handleComment
, BLKformStart  : handleBLKformStart
, BLKformEnd    : handleBLKformEnd
, fn_f          : handleFn_f
, auxilary      : handleAuxilary
, positioning   : handlePositioning
, heidenhain    : _unpack
}

Parse = gen.Parser( heidenhain, {} )
l = gen.Lexer()
