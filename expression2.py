import generator as gen
import CNC
from CNC.language import Arithmetic as cmd
from enum import Enum, unique
import collections

@unique
class ExpressionToken( Enum ):
  plus = '[+]'
  minus = '[-]'

@gen.task.Handler( ExpressionToken )
class ExprHandler:
  def plus( self, task ):
    return cmd.ADD
  def minus( self, task ):
    return cmd.SUB
  
@unique
class TermToken( Enum ):
  mult = '[*]'
  div = '[/]'

@gen.task.Handler( TermToken )
class TermHandler:
  def mult( self, task ):
    return cmd.MUL
  def div( self, task ):
    return cmd.DIV
  
@unique 
class PowToken( Enum ):
  pow = '\\^'

@gen.task.Handler( PowToken )
class PowHandler:
  def pow( self, task ):
    return cmd.POW
  
@unique 
class AssignToken( Enum ):
  assign = '[=]'

@gen.task.Handler( AssignToken )
class AssignHandler:
  def assign( self, task ):
    return cmd.SET

def toFloat( token, state ):
  return [ float( token[0].groups[0] )]
  
expression  = gen.Handle()
term        = gen.Handle()
pow         = gen.Handle()
# ([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))
_number           = gen.make('number')["number"]
_int              = gen.make('int')["number"]
variable          = ( 'Q' & (_int)["sink"])['sink'] & ~( AssignToken & expression )
subexpression     = "(" & expression & ")"

_primary = ( _number | variable | subexpression )["sink"]

expression.rule = ( term & +( ExpressionToken & expression ) )["sink"]
term.rule       = ( pow & +( TermToken & term ) )["sink"]
pow.rule        = ( _primary & +( PowToken & pow ) )["sink"]

handlers = {
  "number"     : toFloat,
  "sink"       : gen.Sink,
  "source"     : gen.Source
}

terminals = {
  "number" : gen.StringTask( '([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))' ),
  'int' : gen.StringTask( '(\\d.)' ),
  'Q'   : gen.StringTask( 'Q' ),
  AssignToken : gen.HandledTask(AssignHandler()),
  '('   : gen.Ignore(gen.StringTask('[(]')),
  ')'   : gen.Ignore(gen.StringTask('[)]')),
  ExpressionToken : gen.HandledTask(ExprHandler()),
  TermToken : gen.HandledTask(TermHandler()),
  PowToken : gen.HandledTask(PowHandler())
}

l = gen.Lexer()

Parse   = gen.Parser( expression, handlers, terminals, gen.Source )
primary = gen.Parser( _primary, handlers, terminals, gen.Source )
number  = gen.Parser( _number, { "number" : toFloat }, terminals, gen.Source )

import time
start = time.time()
for i in range(1000):
  q = Parse(l, "1^(2-3/4)^2/3")
print( str(time.time() - start) )