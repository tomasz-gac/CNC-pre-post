import  languages.expression.grammar      as grammar
import    languages.expression.commands   as cmd

import  generator.terminal as t
import  generator.rule     as r
import  generator.compiler as c

from enum import Enum, unique

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
  'number'          : t.make( '([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))' ) >> t.group(cmd.PUSH),
  'identifier'      : t.make( '(([a-zA-Z_]+\\d*)+)' ) >> t.group( str ),
  'GET'             : t.Return( [cmd.GET] ),
  '='               : tokenLookup( AssignToken ),
  '('               : t.make('[(]').ignore(),
  ')'               : t.make('[)]').ignore(),
  '+-'              : tokenLookup( ExpressionToken ),
  '*/'              : tokenLookup( TermToken ),
  '^'               : tokenLookup( PowToken )
}

compiler = c.Reordering( terminals )

Parse   = t.StrParser( grammar.expression.pull(), compiler )
primary = t.StrParser( grammar.primary.pull(), compiler )
number  = t.StrParser( r.make('number'), compiler )