import generator.rule as r
from generator.grammar import Grammar

g = Grammar()

g.expression  = r.Handle()
g.term        = r.Handle()
g.pow         = r.Handle()

g.get_identifier   = g.identifier, 'GET'
g.set_identifier   = g.identifier.push(), '=', g.expression
g.subexpression      = "(", g.expression, ")"

g.primary = r.make([ g.number, g.set_identifier, g.get_identifier, g.subexpression ]).push()

g.expression.rule = g.term,     +( '+-' & g.term )
g.term.rule       = g.pow,      +( '*/' & g.pow )
g.pow.rule        = g.primary,  +( '^' & g.pow )