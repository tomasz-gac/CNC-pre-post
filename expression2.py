from CNC.language import Arithmetic as cmd
from enum         import Enum, unique
import grammars.math      as math
import generator.terminal as t
import generator.rule     as r
import generator.injector as inj

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
  'setQ'    : t.make( 'Q' ).ignore(cmd.SETQ),
  'getQ'    : t.make( 'Q' ).ignore(cmd.GETQ),
  '='       : tokenLookup( AssignToken ),
  '('       : t.make('[(]').ignore(),
  ')'       : t.make('[)]').ignore(),
  '+-'      : tokenLookup( ExpressionToken ),
  '*/'      : tokenLookup( TermToken ),
  '^'       : tokenLookup( PowToken )
}

inj = inj.ReorderInjector()

Parse   = t.Parser( math.expression.pull(), terminals, inj )
primary = t.Parser( math.primary.pull(), terminals, inj )
number  = t.Parser( r.make('number'), terminals, inj )