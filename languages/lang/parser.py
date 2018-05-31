import re

import languages.lang.grammar as grammar

from generator.terminal import *

import generator.rule     as r
import generator.compiler as c

p = re.compile

identifier_pattern = p('(([a-zA-Z_]+\\d*)+)')
terminal_pattern = p('\'(([a-zA-Z_]+\\d*)+)\'')

unaryOp = Lookup({ 
  p('[+]') : 'Repeat',
  p('[-]') : 'Not',
  p('[~]') : 'Optional',
  p('\\^') : 'Push'
}.items() )

terminals = {
  'terminal'    : If(terminal_pattern, lambda m : m.groups()[0] ),
  'identifier'  : If(identifier_pattern, lambda m : m.groups()[0] ),
  'lookup'      : Return('lookup'),
  
  'assign'      : Return('assign').If(p('[=]')),
  'lparan'      : Return().If(p('[(]')),
  'rparan'      : Return().If(p('[)]')),
  'seq_sep'     : Return('seq_sep').If(p('[,]')),
  'alt_sep'     : Return('alt_sep').If(p('[|]')),
  'unaryOp'     : unaryOp  
}
terminals = pushTerminals(terminals)

compiler = c.Reordering(terminals)
Parse = grammar.grammar.compile(compiler)