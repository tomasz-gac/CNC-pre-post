import generator.rule as r

expression  = r.Handle()
term        = r.Handle()
pow         = r.Handle()

expression.name = 'expression'
term.name = 'term'
pow.name = 'pow'

identifier         = r.Terminal('identifier')
get_identifier     = identifier & 'GET'
set_identifier     = identifier.push() & ('=', expression)
subexpression      = "(" & expression & ")"
subexpression.name = 'subexpression'

primary = ( 'number' | set_identifier | get_identifier | subexpression ).push()
primary.name = 'primary'

expression.rule = term & +( '+-' & term )
term.rule       = pow & +( '*/' & pow )
pow.rule        = primary & +( '^' & pow )