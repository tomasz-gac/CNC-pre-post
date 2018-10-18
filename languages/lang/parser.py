import re

import languages.lang.grammar as grammar

from generator.terminal import *
import generator.evaluator as ev

import generator.rule     as r
import generator.compiler as c

p = re.compile

identifier_pattern = p('(([a-zA-Z_]+\\d*)+)')
terminal_pattern = p('\'(([a-zA-Z_]+\\d*)+)\'')
  
  #function that calls f( last nargs from stack )
def call( f, nargs ):
  def _call( state ):
    args = state.stack[-nargs:]
    del state.stack[-(nargs):]
    state.stack.append(f( *args ))
  return _call

def lookup( state ):
  try:
    state.stack[-1] = state.symtable[state.stack[-1]]
  except KeyError:
      # identifier used for the first time without initiailzation
      # it has to be allowed if we want to have recursive rules
    node = r.Handle()       # identity rule with empty .rule member
    name = state.stack[-1]
    node.name = name
    state.symtable[ name ] = node
    state.stack[-1] = node

def terminal( match ):
  def make_terminal( state ):
    state.stack.append( r.Terminal( match.groups()[0] ) )
  return make_terminal,

def identifier( match ):
  def id_push( state ):
    state.stack.append( match.groups()[0] )
  return id_push,
  
def assign( state ):
  name, rhs = state.stack[-2:]
  del state.stack[-2:]
  if name in state.symtable:
    lhs = state.symtable[name]
      # lhs has already been used, but is uninitialized
    if isinstance( lhs, r.Handle ) and lhs.rule is None:
      lhs.rule = rhs
    else:
      raise RuntimeError('Symbol "'+ name +'" already defined')
  else:
    state.symtable[ name ] = rhs
    state.symtable[ name ].name = name
    
unaryOp = Lookup({ 
  p('[*]') : (call(r.Repeat, 1),),
  p('[!]') : (call(r.Not, 1),),
  p('[?]') : (call(r.Optional, 1),),
  p('\\^') : (call(r.Push, 1),)
}.items() )

terminals = {
  'terminal'    : If(terminal_pattern, terminal ),
  'identifier'  : If(identifier_pattern, identifier ),
  'lookup'      : Return(lookup),
  
  'assign'      : Return(assign).If(p('[=]')),
  'lparan'      : Return().If(p('[(]')),
  'rparan'      : Return().If(p('[)]')),
  'seq_sep'     : Return(call( r.Sequence, 2 )),
  'alt_sep'     : Return(call( r.Alternative, 2 )).If(p('[/]')),
  'unaryOp'     : unaryOp
}
# terminals = pushTerminals(terminals)

compiler = c.Reordering(terminals)
Parse = grammar.grammar.compile(compiler)