from CNC.language import Arithmetic as cmd
from enum import Enum, unique
import grammars.math as math
import generator as gen

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
  AssignToken.assign    : cmd.LET
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
  'number'  : gen.make_terminal( '([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))' ) >> gen.group(0) >> float,
  'int'     : gen.make_terminal( '(\\d.)' ) >> gen.group(0) >> int,
  'setQ'    : gen.make_terminal( 'Q' ).ignore(cmd.SETQ),
  'getQ'    : gen.make_terminal( 'Q' ).ignore(cmd.GETQ),
  '='       : tokenLookup( AssignToken ),
  '('       : gen.StringTask('[(]').ignore(),
  ')'       : gen.StringTask('[)]').ignore(),
  '+-'      : tokenLookup( ExpressionToken ),
  '*/'      : tokenLookup( TermToken ),
  '^'       : tokenLookup( PowToken )
}

l = gen.Lexer()

Parse   = gen.Parser( math.expression['source'], terminals, handlers )
primary = gen.Parser( math._primary['source'], terminals, handlers )
number  = gen.Parser( gen.make('number'), terminals, handlers )