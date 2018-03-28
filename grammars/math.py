import generator.rule as r

expression  = r.Handle()
term        = r.Handle()
pow         = r.Handle()

expression.name = 'expression'
term.name = 'term'
pow.name = 'pow'

_int          = r.make('int')
getQ          = ( 'getQ' & _int.push()).push()
setQ          = ((( 'setQ' & _int.push(2)).push(2) & '=').push(2) & expression).pull(2)
subexpression = "(" & expression & ")"
subexpression.name = 'subexpression'

primary = ( 'number' | setQ | getQ | subexpression ).push()
primary.name = 'primary'

expression.rule = ( term & +( '+-' & expression ) ).push()
term.rule       = ( pow & +( '*/' & term ) ).push()
pow.rule        = ( primary & +( '^' & pow ) ).push()
