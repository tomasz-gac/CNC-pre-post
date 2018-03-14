import generator as gen
import CNC
from enum import Enum, unique
import collections

@unique
class ExpressionTokens( Enum ):
  plus = '[+]'
  minus = '[-]'

@unique
class TermTokens( Enum ):
  mult = '[*]'
  div = '[/]'

def toFloat( token ):
  return float( token.groups[0] )
    
expression  = gen.Handle()
term        = gen.Handle()
pow         = gen.Handle()

_number           = gen.make('([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))')
variable          = 'Q(\\d+)' & ~( gen.Ignore("[=]") & expression )
subexpression     = gen.Ignore("[(]") & [ expression, gen.Ignore("[)]") ]

_primary = gen.Bracket( _number | [ variable, subexpression ] )
_primary.name = "primary"

expression.rule = gen.Bracket( term & +( ExpressionTokens & term ) )
term.rule       = gen.Bracket( pow & +( TermTokens & pow ) )
pow.rule        = gen.Bracket( _primary & +( "\\^" & _primary ) )

'''expression.rule = gen.Bracket( term & [ ExpressionTokens , expression ] | term )
term.rule       = gen.Bracket( pow & [ TermTokens, term ] | pow )
pow.rule        = gen.Bracket( _primary & [ "\\^", pow ] | _primary )'''

expression.name =  "expression"
term.name =  "term"
pow.name =  "pow"


handlers = {
  _number     : toFloat
}

l = gen.Lexer()

Parse   = gen.Parser( expression, handlers )
primary = gen.Parser( _primary, handlers )
number  = gen.Parser( _number, { _number : toFloat } )