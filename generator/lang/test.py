import generator.lang.grammar as g
import generator.lang.parser as p

test = """
  sequence = rule *( 'seq_sep' ^rule )
  alternative = sequence *( 'alt_sep' ^sequence )
  get_identifier = 'identifier' 'lookup'
  primary = ^( 'lparan' ^alternative 'rparan' / 'terminal' / get_identifier )
  rule = ^( ?'unaryOp' primary )
  grammar = ^'identifier' 'assign' ^alternative
"""

first = p.parseStr( test )
g1 = first.symtable['grammar']

Parse = g1.compile( p.compiler )

second = p.parseStr( test, Parse )
g2 = second.symtable['grammar'] 