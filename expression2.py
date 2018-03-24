from CNC.language import Arithmetic as cmd
from enum import Enum, unique
import grammars.math as math
import generator as gen
import generator.terminal as t
import generator.rule as r

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

handlers = {
  "sink"       : gen.Sink,
  "source"     : gen.Source
}

def p( x ):
  def impl( ret ):
    print(x)
    return ret
  return impl

terminals = {
  'number'  : t.make( '([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))' ) >> gen.group(float),
  'int'     : t.make( '(\\d.)' ) >> gen.group(int),
  'setQ'    : t.make( 'Q' ).ignore(cmd.SETQ),
  'getQ'    : t.make( 'Q' ).ignore(cmd.GETQ),
  '='       : tokenLookup( AssignToken ),
  '('       : t.make('[(]').ignore(),
  ')'       : t.make('[)]').ignore(),
  '+-'      : tokenLookup( ExpressionToken ),
  '*/'      : tokenLookup( TermToken ),
  '^'       : tokenLookup( PowToken )
}

inj = gen.ReorderInjector()

Parse   = gen.Parser( math.expression.pull(), terminals, inj )
primary = gen.Parser( math._primary.pull(), terminals, inj )
number  = gen.Parser( r.make('number'), terminals, inj )