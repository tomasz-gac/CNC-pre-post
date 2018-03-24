import generator as gen
import generator.rule as r

expression  = r.Handle()
term        = r.Handle()
pow         = r.Handle()

_int          = r.make('int').push()
getQ          = ( 'getQ' & _int).push()
setQ          = ( 'setQ' & _int).push() & '=' & expression
subexpression = "(" & expression & ")"

_primary = ( 'number' | setQ | getQ | subexpression ).push()

expression.rule = ( term & +( '+-' & expression ) ).push()
term.rule       = ( pow & +( '*/' & term ) ).push()
pow.rule        = ( _primary & +( '^' & pow ) ).push()
