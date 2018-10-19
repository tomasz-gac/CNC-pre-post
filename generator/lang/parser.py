import re

import generator.lang.grammar as grammar

from generator.terminal import *

import generator.rule     as r
import generator.compiler as c
import generator.state    as s

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

  # function will prevent nesting of n-ary rules: sequence(sequence(1,2),3) -> sequence(1,2,3)
  # by appending values from stack to the top-level rule's children
  # if the top-level rule's type matches to 'Class' 
  # and the appended rule is not recursively called
def nest_nonrecursive( Class ):
  def _append( state ):
    lhs, rhs = state.stack[-2], state.stack[-1]
    if isinstance( lhs, Class ):
        # append if the rule has not been defined as a symbol
        # if it has not, then it cannot be called recursively
      if lhs not in state.symtable.values():
        rules = lhs.rules
        lhs.rules = (*rules, rhs)
        del state.stack[-1]
        return
    # otherwise - wrap args into Class
    args = state.stack[-2:]
    del state.stack[-2:]
    state.stack.append(Class( *args ))
  return _append
        
  
def lookup( state ):
  try:
    state.stack[-1] = state.symtable[state.stack[-1]]
  except KeyError:
      # identifier used for the first time without initiailzation
      # it has to be allowed if we want to have recursive rules
    name = state.stack[-1]  
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

def make_symbol( state ):
  name = state.stack[-1]
  if name in state.symtable:
    raise RuntimeError('Symbol "' + name + '" already defined')
  del state.stack[-1]
  state.symtable[name] = r.Handle()
  state.symtable[name].name = name

terminals = {
  'terminal'    : If(terminal_pattern, terminal ),
  'identifier'  : If(identifier_pattern, identifier ),
  'lookup'      : Return(lookup),
  
  'assign'      : Return(assign).If(p('[=]')),
  'lparan'      : Return().If(p('[(]')),
  'rparan'      : Return().If(p('[)]')),
  'seq_sep'     : Return(nest_nonrecursive( r.Sequence )),
  'alt_sep'     : Return(nest_nonrecursive( r.Alternative )).If(p('[/]')),
  'unaryOp'     : unaryOp
}
# terminals = pushTerminals(terminals)

compiler = c.Reordering(terminals)
Parse = grammar.grammar.compile(compiler)

def parseStr( input, parser = Parse ):
  state = s.State('')
  for line in input.splitlines():
    if len(line) == 0:
      continue
    state.input = line
    parser( state )
    if len(state.input) > 0:
      raise RuntimeError('Partial parse: "'+state.input+'"')
  
    #check for undefined variables
  for name, value in state.symtable.items():
    if isinstance( value, r.Handle ):
      if value.rule is None:
        raise RuntimeError( 'Uninitialized variable "'+name+'"' )
  return state