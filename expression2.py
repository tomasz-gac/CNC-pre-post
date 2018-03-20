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
  return float( token.groups[0] ), state
    
expression  = gen.Handle()["source"]
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

'''expression.rule = ( term & [ ExpressionTokens , expression ] | term ).push()
term.rule       = ( pow & [ TermTokens, term ] | pow ).push()
pow.rule        = ( _primary & [ PowTokens, pow ] | _primary ).push()'''

class Source:    
  def __init__( self, sink ):
    self._sink = sink
  
  @property
  def sink( self ):
    return self._sink

  def __call__( self, fallthrough, state ):
    if gen.ParserFailed( fallthrough, True ):
      return gen.ParserFailed
    if fallthrough is not None:
      raise RuntimeError("Parser returned with fallthrough:" + str(fallthrough) )
    # 
    return self.sink.extract(state), state

class Sink:
  def __call__( self, result, state ):  
    if gen.ParserFailed( result, True ):
      return ParserFailed
    elif result is not None:
      try:
        state[self] += result
      except KeyError:
        state[self] = result
    return None, state
    
  def extract( self, state ):
    result = state[self]
    del state[self]
    return result
    
  def clear( self, state ):
    del state[self]

def Pipe():
  s = Sink()
  return s, Source(s)
  
sink, source = Pipe()
    
handlers = {
  "number"     : toFloat,
  "sink"       : sink,
  "source"     : source
}

l = gen.Lexer()

Parse   = gen.Parser( expression, handlers )
primary = gen.Parser( _primary, handlers )
number  = gen.Parser( _number["sink"], { _number : toFloat } )