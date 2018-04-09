import  languages.expression.grammar  as grammar
import  languages.expression.commands as cmd

import  generator.terminal as t
import  generator.rule     as r
import  generator.compiler as c

expressionToken = t.Pattern({
  '[+]' : t.Return( cmd.ADD ),
  '[-]' : t.Return( cmd.SUB )
})

termToken = t.Pattern({
  '[*]' : t.Return( cmd.MUL ),
  '[/]' : t.Return( cmd.DIV )
})

powToken = t.Pattern({ '\\^' : t.Return( cmd.POW ) })

assignToken = t.Pattern({ '[=]' : t.Return( cmd.LET )} )
number = t.Pattern({ 
  '([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))' : (lambda match : [ cmd.PUSH(float(match.groups()[0])) ]) 
})
identifier = t.Pattern({ 
  '(([a-zA-Z_]+\\d*)+)' : (lambda match : [ cmd.PUSH(match.groups()[0]) ]) 
})

terminals = {
  'number'          : number,
  'identifier'      : identifier,
  'GET'             : t.Return( [cmd.GET] ),
  '='               : assignToken,
  '('               : t.Pattern({ '[(]' : t.Return() }),
  ')'               : t.Pattern({ '[)]' : t.Return() }),
  '+-'              : expressionToken,
  '*/'              : termToken,
  '^'               : powToken
}

compiler = c.Reordering( terminals )

Parse   = t.EagerParser( grammar.expression, compiler )
primary = t.EagerParser( grammar.primary, compiler )
number  = t.EagerParser( r.make('number'), compiler )