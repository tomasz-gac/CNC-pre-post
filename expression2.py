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

def toFloat( token, state ):
  return [ float( token[0].groups[0] )]
    
expression  = gen.Handle()
term        = gen.Handle()
pow         = gen.Handle()

_number           = gen.make('([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))')["number"]
_int              = gen.make('(\\d+)')["number"]
variable          = 'Q' & (_int)["sink"] & ~( AssignHandler() & expression )
subexpression     = gen.Ignore("[(]") & [ expression, gen.Ignore("[)]") ]

_primary = ( _number | [ variable, subexpression ] )["sink"]

expression.rule = ( term & +( ExprHandler() & expression ) )["sink"]
term.rule       = ( pow & +( TermHandler() & term ) )["sink"]
pow.rule        = ( _primary & +( PowHandler() & pow ) )["sink"]

handlers = {
  "number"     : toFloat,
  "sink"       : gen.Sink,
  "source"     : gen.Source
}

l = gen.Lexer()

Parse   = gen.Parser( expression, handlers, gen.Source )
primary = gen.Parser( _primary, handlers, gen.Source )
number  = gen.Parser( _number, { "number" : toFloat }, gen.Source )

import time
start = time.time()
for i in range(1000):
  q = Parse(l, "1^(2-3/4)^2/3")
print( str(time.time() - start) )