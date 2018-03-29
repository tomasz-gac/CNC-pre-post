from CNC.language import Commands as cmd
from enum         import Enum, unique
import grammars.math      as math
import generator.terminal as t
import generator.rule     as r
import generator.compiler as c

@unique
class ExpressionToken( Enum ):
  plus = '[+]'
  minus = '[-]'
  
@unique
class TermToken( Enum ):
  mult = '[*]'
  div = '[/]'
  
@unique 
class PowToken( Enum ):
  pow = '\\^'
  
@unique 
class AssignToken( Enum ):
  assign = '[=]'
  
tokenLookup = t.make_lookup( { 
  ExpressionToken.plus  : [ cmd.ADD ], 
  ExpressionToken.minus : [ cmd.SUB ], 
  TermToken.mult        : [ cmd.MUL ], 
  TermToken.div         : [ cmd.DIV ], 
  PowToken.pow          : [ cmd.POW ], 
  AssignToken.assign    : [ cmd.LET ]
} )


terminals = {
  'number'  : t.make( '([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))' ) >> t.group(float),
  'int'     : t.make( '(\\d.)' ) >> t.group(int),
  'setQ'    : t.make( 'Q' ).ignore([cmd.SETQ]),
  'getQ'    : t.make( 'Q' ).ignore([cmd.GETQ]),
  '='       : tokenLookup( AssignToken ),
  '('       : t.make('[(]').ignore(),
  ')'       : t.make('[)]').ignore(),
  '+-'      : tokenLookup( ExpressionToken ),
  '*/'      : tokenLookup( TermToken ),
  '^'       : tokenLookup( PowToken )
}

compiler = c.Reordering( terminals )

Parse   = t.StrParser( math.expression.pull(), compiler )
primary = t.StrParser( math.primary.pull(), compiler )
number  = t.StrParser( r.make('number'), compiler )