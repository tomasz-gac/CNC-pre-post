import  languages.expression.grammar  as grammar
import  languages.expression.commands as cmd

from generator.terminal import *
import  generator.rule as r
import  generator.compiler as c
import  generator.evaluator as ev

expressionToken = Switch({
  '[+]' : Return( cmd.ADD ),
  '[-]' : Return( cmd.SUB )
})

termToken = Switch({
  '[*]' : Return( cmd.MUL ),
  '[/]' : Return( cmd.DIV )
})

powToken = Switch({ '\\^' : Return( cmd.POW ) })

assignToken = Switch({ '[=]' : Return( cmd.LET )} )
number = Switch({ 
  '([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))' : (lambda match : [ cmd.PUSH(float(match.groups()[0])) ]) 
})
identifier = Switch({ 
  '(([a-zA-Z_]+\\d*)+)' : (lambda match : [ cmd.PUSH(match.groups()[0]) ]) 
})

terminals = {
  'number'          : number,
  'identifier'      : identifier,
  'GET'             : Return( [cmd.GET] ),
  '='               : assignToken,
  '('               : Switch({ '[(]' : Return() }),
  ')'               : Switch({ '[)]' : Return() }),
  '+-'              : expressionToken,
  '*/'              : termToken,
  '^'               : powToken
}

compiler = c.Reordering( terminals )

Parse   = Parser( grammar.expression, ev.Eager, compiler )
primary = Parser( grammar.primary, ev.Eager, compiler )
number  = Parser( r.make('number'), ev.Eager, compiler )