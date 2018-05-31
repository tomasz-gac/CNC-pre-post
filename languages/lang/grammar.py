import generator.rule as r

terminal    = r.Terminal('terminal')
identifier  = r.Terminal('identifier')
lookup      = r.Terminal('lookup')
assign      = r.Terminal('assign')
seq_sep     = r.Terminal('seq_sep')
alt_sep     = r.Terminal('alt_sep')
lparan      = r.Terminal('lparan')
rparan      = r.Terminal('rparan')

unaryOp = r.Terminal('unaryOp')

rule = r.Handle()
rule.name = 'rule'

alternative = r.Sequence( (rule, r.Repeat(r.Sequence( (alt_sep, r.Push(rule)) ))) )
alternative.name = 'alternative'
sequence    = r.Sequence( (alternative, r.Repeat(r.Sequence( (seq_sep, r.Push(alternative)) ))) )
sequence.name = 'sequence'

get_identifier = r.Sequence( (identifier, lookup ) )
get_identifier.name = 'get_identifier'

primary = r.Push(r.Alternative( ( 
  r.Sequence( (lparan, r.Push(sequence), rparan) ), 
  r.Alternative( ( terminal, get_identifier ) ) 
)))

primary.name = 'primary'

rule.rule = r.Push( r.Sequence((r.Optional( unaryOp ), primary )) )

grammar = r.Sequence( ( r.Push( identifier ), assign, r.Push(sequence) ) )
grammar.name = 'grammar'
