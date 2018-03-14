import generator as gen
import CNC
from enum import Enum, unique

@unique
class ExpressionTokens( Enum ):
  plus = '[+]'
  minus = '[-]'

@unique
class TermTokens( Enum ):
  mult = '[*]'
  div = '[/]'

def toFloat( token ):
  return float( token.groups[0] )
  
def handleNumber( token ):
  return CNC.AST.ExprTerminal( toFloat(token) )

def handleVariable( lst ):
  N = int( lst[0].groups[0])
  rhs = lst[1]
  if rhs is not None:
    return CNC.AST.ExprBinary( CNC.AST.ExprVariable(N), list(rhs)[1], CNC.AST.ExprOperators.assign )
  else:
    return CNC.AST.ExprVariable( N )
    
def handleExpression( gen ):
    # expression is a gen.Handle so the .rule returns an iterable
  result = next(gen)    # first number
  pairs = zip(gen,gen)  # zip into list of pairs (token, value)
  for token, value in pairs:
    result = CNC.AST.ExprBinary( result, value
    , CNC.AST.ExprOperators.plus if token.type is ExpressionTokens.plus else CNC.AST.ExprOperators.minus
    )
  return result

def handleSubexpression( gen ):
  # unwrap the gen == ["(", expr, ")"]
  # and wrap it as an iterable handleExpression expects
  return handleExpression(iter([list(gen)[1]]))
  
def handleTerm( gen ):
  result = next(gen)
  pairs = zip(gen,gen)
  for token, value in pairs:
    result = CNC.AST.ExprBinary( result, value
    , CNC.AST.ExprOperators.mult if token.type is TermTokens.mult else CNC.AST.ExprOperators.div
    )
  return result

def handlePow( gen ):
  result = next(gen)
  for value in ( x for x in gen if x is not None):
    result = CNC.AST.ExprBinary( result, value, CNC.AST.ExprOperators.pow )
  return result
    
expression  = gen.Handle()
term        = gen.Handle()
pow         = gen.Handle()

_number           = gen.make('([+-]?((\\d+[.]\\d*)|([.]\\d+)|(\\d+)))')
variable          = 'Q(\\d+)' & ~( gen.Ignore("[=]") & expression )
subexpression     = gen.Ignore("[(]") & [ expression, gen.Ignore("[)]") ]

_primary = _number | [ variable, subexpression ]

expression.rule = term & +( ExpressionTokens & expression )
term.rule       = pow & +( TermTokens & term )
pow.rule        = _primary & +( gen.Ignore("\\^") & pow )

handlers = {
  _number       : handleNumber
, variable      : handleVariable
, expression    : handleExpression
, term          : handleTerm
, pow           : handlePow
, subexpression : handleSubexpression
}

Parse   = gen.Parser( expression, handlers )
primary = gen.Parser( _primary, handlers )
number  = gen.Parser( _number, { _number : toFloat } )