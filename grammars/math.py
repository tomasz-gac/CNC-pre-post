import generator as gen
import generator.rule as r

expression  = r.Handle()
term        = r.Handle()
pow         = r.Handle()

_int          = r.make('int')['sink']
getQ          = ( 'getQ' & _int)['sink'] 
setQ          = ( 'setQ' & _int)['sink'] & '=' & expression
subexpression = "(" & expression & ")"

_primary = ( 'number' | setQ | getQ | subexpression )["sink"]

expression.rule = ( term & +( '+-' & expression ) )["sink"]
term.rule       = ( pow & +( '*/' & term ) )["sink"]
pow.rule        = ( _primary & +( '^' & pow ) )["sink"]
