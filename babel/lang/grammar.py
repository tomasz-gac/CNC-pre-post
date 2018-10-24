import babel.rule as r

terminal    = r.Terminal('terminal')
identifier  = r.Terminal('identifier')
lookup      = r.Terminal('lookup')
assign      = r.Terminal('assign')
seq_sep     = r.Terminal('seq_sep')
alt_sep     = r.Terminal('alt_sep')
lparan      = r.Terminal('lparan')
rparan      = r.Terminal('rparan')
handle      = r.Terminal('handle')

unaryOp = r.Terminal('unaryOp')

rule = r.Handle()
rule.name = 'rule'

sequence    = r.Sequence( rule, r.Repeat(r.Sequence( seq_sep, r.Push(rule) )) )
sequence.name = 'sequence'
alternative = r.Sequence( sequence, r.Repeat(r.Sequence( alt_sep, r.Push(sequence) )) )
alternative.name = 'alternative'

get_identifier = r.Sequence( identifier, lookup )
get_identifier.name = 'get_identifier'

primary = r.Push(r.Alternative( 
  r.Sequence( lparan, r.Push(alternative), rparan ), 
  terminal, 
  get_identifier
))

primary.name = 'primary'

rule.rule = r.Push( r.Alternative( r.Sequence( unaryOp, rule ), primary ) )

grammar = r.Sequence( r.Push( identifier ), assign, r.Push(alternative) )
grammar.name = 'grammar'
