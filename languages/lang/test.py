import languages.lang.grammar as g
import languages.lang.parser as p
import generator.state as s
import generator.rule as r

def parse( input, parser = p.Parse ):
  state = s.State('')
  for line in input.splitlines():
    state.input = line
    p.Parse( state )
    if len(state.input) > 0:
      raise RuntimeError('Partial parse: "'+state.input+'"')
  
    #check for undefined variables
  for name, value in state.symtable.items():
    if isinstance( value, r.Handle ):
      if value.rule is None:
        raise RuntimeError( 'Uninitialized variable "'+name+'"' )
  return state
    

test = """sequence = rule *( 'seq_sep' ^rule )
alternative = sequence *( 'alt_sep' ^sequence )
get_identifier = 'identifier' 'lookup'
primary = ^( 'lparan' ^alternative 'rparan' / 'terminal' / get_identifier )
rule = ^( ?'unaryOp' primary )
grammar = ^'identifier' 'assign' ^alternative
"""

first = parse( test )

Parse = grammar.compile( p.compiler )

second = parse( test, Parse )
g1 = first.symtable['grammar']
g2 = second.symtable['grammar']