import generator.rule as r

expression  = r.Handle()
term        = r.Handle()
pow         = r.Handle()

expression.name = 'expression'
term.name = 'term'
pow.name = 'pow'

_int          = r.make('int').push()
getQ          = ( 'getQ' & _int).push()
setQ          = ( 'setQ' & _int).push() & '=' & expression
subexpression = "(" & expression & ")"
subexpression.name = 'subexpression'

primary = ( 'number' | setQ | getQ | subexpression ).push()
primary.name = 'primary'

expression.rule = ( term & +( '+-' & expression ) ).push()
term.rule       = ( pow & +( '*/' & term ) ).push()
pow.rule        = ( primary & +( '^' & pow ) ).push()
