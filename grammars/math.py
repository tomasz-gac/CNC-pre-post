import generator as gen

expression  = gen.Handle()
term        = gen.Handle()
pow         = gen.Handle()

_int          = gen.make('int')['sink']
getQ          = ( 'getQ' & _int)['sink'] 
setQ          = ( 'setQ' & _int)['sink'] & '=' & expression
subexpression = "(" & expression & ")"

_primary = ( 'number' | setQ | getQ | subexpression )["sink"]

expression.rule = ( term & +( '+-' & expression ) )["sink"]
term.rule       = ( pow & +( '*/' & term ) )["sink"]
pow.rule        = ( _primary & +( '^' & pow ) )["sink"]
