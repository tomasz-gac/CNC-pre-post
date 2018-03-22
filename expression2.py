import generator as gen
import CNC
from CNC.language import Arithmetic as cmd
from enum import Enum, unique
import collections

expression  = gen.Handle()
term        = gen.Handle()
pow         = gen.Handle()

_int          = gen.make('int')
variable      = ( 'Q' & _int['sink'])['sink'] & ~( '=' & expression )
subexpression = "(" & expression & ")"

_primary = ( 'number' | variable | subexpression )["sink"]

expression.rule = ( term & +( '+-' & expression ) )["sink"]
term.rule       = ( pow & +( '*/' & term ) )["sink"]
pow.rule        = ( _primary & +( '^' & pow ) )["sink"]

handlers = {
  "sink"       : gen.Sink,
  "source"     : gen.Source
}

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
  
tokenLookup = gen.makeLookup( { 
  ExpressionToken.plus  : cmd.ADD, 
  ExpressionToken.minus : cmd.SUB, 
  TermToken.mult        : cmd.MUL, 
  TermToken.div         : cmd.DIV, 
  PowToken.pow          : cmd.POW, 
  AssignToken           : cmd.SET
} )

terminals = {
  'number'  : gen.make_terminal( '([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))' ) >> gen.group(0) >> float,
  'int'     : gen.make_terminal( '(\\d.)' ) >> gen.group(0) >> int,
  'Q'       : gen.make_terminal( 'Q' ),
  '='       : tokenLookup( AssignToken ),
  '('       : gen.StringTask('[(]').ignore(),
  ')'       : gen.StringTask('[)]').ignore(),
  '+-'      : tokenLookup( ExpressionToken ),
  '*/'      : tokenLookup( TermToken ),
  '^'       : tokenLookup( PowToken )
}

l = gen.Lexer()

Parse   = gen.Parser( expression['source'], terminals, handlers )
primary = gen.Parser( _primary['source'], terminals, handlers )
number  = gen.Parser( gen.make('number') , handlers, terminals )

import time
start = time.time()
for i in range(1000):
  q = Parse(l, "1^(2-3/4)^2/3")
print( str(time.time() - start) )