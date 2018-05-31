import languages.lang.grammar as g
import languages.lang.parser as p
import generator.state as s

state = s.State("a = 'test'")
p.Parse( state )
print(state.input)
print(state.stack)

state = s.State("a = 'test', 'best'")
p.Parse( state )
print(state.input)
print(state.stack)

state = s.State("a = 'test', 'best' | 'detest'")
p.Parse( state )
print(state.input)
print(state.stack)
