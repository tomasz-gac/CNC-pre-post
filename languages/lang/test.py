import languages.lang.grammar as g
import languages.lang.parser as p
import generator.state as s
import generator.rule as r

def parse( input ):
  state = s.State('')
  for line in input.splitlines():
    state.input = line
    p.Parse( state )
  
    #check for undefined variables
  for name, value in state.symtable.items():
    if isinstance( value, r.Handle ):
      if value.rule is None:
        raise RuntimeError( 'Uninitialized variable "'+name+'"' )
  return state
    

test = """a = 'test'
b = 'test' 'best'
c = 'test' 'best' / 'detest'
d = d
e = *e 'das'
f = *( ?'das' 'das' / 'ssd' ) f
g = 'dsa' / 'dds' / 'asd'
"""

r = parse( test )
globals().update(r.symtable)