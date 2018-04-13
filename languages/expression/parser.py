import  re

import  languages.expression.grammar  as grammar
import  languages.expression.commands as cmd

from generator.terminal import *
import  generator.rule      as r
import  generator.compiler  as c

p = re.compile

number_pattern = p('([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))')
identifier_pattern = p('(([a-zA-Z_]+\\d*)+)')

terminals = {
  'number'      : If(number_pattern,     lambda match : (Push(float(match.groups()[0])),) ),
  'identifier'  : If(identifier_pattern, lambda match : (Push(match.groups()[0]),)),
  'GET'         : Return(cmd.GET),
  
  '='           : Return(cmd.LET).If(p('[=]')),
  '('           : Return().If(p('[(]')),
  ')'           : Return().If(p('[)]')),
  
  '+-'          : Lookup( {p('[+]') : (cmd.ADD,), p('[-]') : (cmd.SUB,)}.items() ),
  '*/'          : Lookup( {p('[*]') : (cmd.MUL,), p('[/]') : (cmd.DIV,)}.items() ),
  '^'           : If(p('\\^'), Return(cmd.POW))
}

compiler = c.Reordering( terminals )

Parse   = grammar.expression.compile( compiler )
primary = grammar.primary.compile( compiler )
number  = r.Terminal('number').compile( compiler )