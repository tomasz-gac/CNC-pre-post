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

def toFloat( token ):
  return [ cmd.PUSH, float( token.groups[0] ) ]
    
expression  = gen.Handle()
term        = gen.Handle()
pow         = gen.Handle()

_number           = gen.make('([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))')
_int              = gen.make('(\\d+)')
variable          = 'Q' & gen.Push(_int) & ~( AssignHandler() & expression )
subexpression     = gen.Ignore("[(]") & [ expression, gen.Ignore("[)]") ]

_primary = gen.Push( _number | [ variable, subexpression ] )
_primary.name = "primary"

expression.rule = gen.Push( term & +( ExprHandler() & expression ) )
term.rule       = gen.Push( pow & +( TermHandler() & term ) )
pow.rule        = gen.Push( _primary & +( PowHandler() & pow ) )

'''expression.rule = gen.Push( term & [ ExpressionTokens , expression ] | term )
term.rule       = gen.Push( pow & [ TermTokens, term ] | pow )
pow.rule        = gen.Push( _primary & [ PowTokens, pow ] | _primary )'''

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