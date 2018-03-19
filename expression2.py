import generator as gen
import CNC
from CNC.language import Arithmetic as cmd
from enum import Enum, unique
import collections

@unique
class ExpressionTokens( Enum ):
  plus = '[+]'
  minus = '[-]'

@gen.task.Handler( ExpressionTokens )
class ExprHandler:
  def plus( self, task ):
    return cmd.ADD
  def minus( self, task ):
    return cmd.SUB
  
@unique
class TermTokens( Enum ):
  mult = '[*]'
  div = '[/]'

@gen.task.Handler( TermTokens )
class TermHandler:
  def mult( self, task ):
    return cmd.MUL
  def div( self, task ):
    return cmd.DIV
  
@unique 
class PowTokens( Enum ):
  pow = '\\^'

@gen.task.Handler( PowTokens )
class PowHandler:
  def pow( self, task ):
    return cmd.POW
  
@unique 
class AssignTokens( Enum ):
  assign = '[=]'

@gen.task.Handler( AssignTokens )
class AssignHandler:
  def assign( self, task ):
    return cmd.SET

def toFloat( token, result ):
  return float( token.groups[0] ), result
    
expression  = gen.Handle()
term        = gen.Handle()
pow         = gen.Handle()

_number           = gen.make('([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))')
_int              = gen.make('(\\d+)')
variable          = 'Q' & (_int).push() & ~( AssignHandler() & expression )
subexpression     = gen.Ignore("[(]") & [ expression, gen.Ignore("[)]") ]

_primary = ( _number | [ variable, subexpression ] ).push()
_primary.name = "primary"

expression.rule = ( term & +( ExprHandler() & expression ) ).push()
term.rule       = ( pow & +( TermHandler() & term ) ).push()
pow.rule        = ( _primary & +( PowHandler() & pow ) ).push()

'''expression.rule = ( term & [ ExpressionTokens , expression ] | term ).push()
term.rule       = ( pow & [ TermTokens, term ] | pow ).push()
pow.rule        = ( _primary & [ PowTokens, pow ] | _primary ).push()'''

expression.name =  "expression"
term.name =  "term"
pow.name =  "pow"


handlers = {
  _number     : toFloat,
  _int        : toFloat
}

l = gen.Lexer()

Parse   = gen.Parser( expression, handlers )
primary = gen.Parser( _primary, handlers )
number  = gen.Parser( gen.Push(_number), { _number : toFloat } )