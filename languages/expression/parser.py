import  languages.expression.grammar  as grammar
import  languages.expression.commands as cmd

import  generator.terminal as t
import  generator.rule     as r
import  generator.compiler as c

class Return:
  def __init__( self, value ):
    self.returned = value
    
  def __call__( self, *args ):
    return self.returned

expressionToken = t.Pattern({
  '[+]' : t.ret( cmd.ADD ),
  '[-]' : t.ret( cmd.SUB )
})

termToken = t.Pattern({
  '[*]' : t.ret( cmd.MUL ),
  '[/]' : t.ret( cmd.DIV )
})

powToken = t.Pattern({ '\\^' : t.ret( cmd.POW ) })

assignToken = t.Pattern({ '[=]' : t.ret( cmd.LET )} )
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
  '('               : t.Pattern({ '[(]' : t.ret() }),
  ')'               : t.Pattern({ '[)]' : t.ret() }),
  '+-'              : expressionToken,
  '*/'              : termToken,
  '^'               : powToken
}

compiler = c.Reordering( terminals )

Parse   = t.StrParser( grammar.expression, compiler )
primary = t.StrParser( grammar.primary, compiler )
number  = t.StrParser( r.make('number'), compiler )