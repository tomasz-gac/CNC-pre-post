import  re

# import  languages.expression.grammar  as grammar
import  languages.expression.commands as cmd

from babel.terminal import *
import  babel.rule      as r
import  babel.compiler  as c

import babel.lang.parser as p

with open( 'languages/expression/expression.lang' ) as file:
  lang = p.parseStr( file.read() )
  globals().update( lang.symtable )

p = re.compile

number_pattern = p('([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))')
identifier_pattern = p('(([a-zA-Z_]+\\d*)+)')

def number( state ):
  match = number_pattern.match( state.input )
  if match is not None:
    state.input = match.string[match.end(0):]
    return (Push(float(match.groups()[0])),)
  
  raise ParserFailedException('Number not matched')

def identifier( state ):
  match = identifier_pattern.match( state.input )
  if match is not None:
    state.input = match.string[match.end(0):]
    return (Push(match.groups()[0]),)
  
  raise ParserFailedException('Identifier not matched')
    
terminals = {
  'number'      : number,
  'identifier'  : identifier,
  'GET'         : Return(cmd.GET),
  
  'assign'      : Return(cmd.LET).If(p('[=]')),
  'lpar'        : Return().If(p('[(]')),
  'rpar'        : Return().If(p('[)]')),
  
  'plusminus'   : Lookup( {p('[+]') : (cmd.ADD,), p('[-]') : (cmd.SUB,)}.items() ),
  'muldiv'      : Lookup( {p('[*]') : (cmd.MUL,), p('[/]') : (cmd.DIV,)}.items() ),
  'power'       : If(p('\\^'), Return(cmd.POW))
}

compiler = c.Reordering( terminals )

Parse   = expression.compile( compiler )
primary = primary.compile( compiler )
number  = r.Terminal('number').compile( compiler )