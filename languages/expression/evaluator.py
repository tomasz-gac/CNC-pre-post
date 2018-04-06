import generator.evaluator as ev
from languages.expression.commands import Arithmetic

@ev.Handler( Arithmetic )
class ArithmeticEvaluator:
  def __init__( self, symtable ):
    self.symtable = symtable
  
  @ev.stack2args(2)
  def ADD( self, A, B ):
    return [ A + B ]
  
  @ev.stack2args(2)
  def SUB( self, A, B ):
    return [ A - B ]
  
  @ev.stack2args(2)
  def MUL( self, A, B ):
    return [ A * B ]
  
  @ev.stack2args(2)
  def DIV( self, A, B ):
    return [ A / B ]
  
  @ev.stack2args(2)
  def POW( self, A, B ):
    return [ A ** B ]
    
  @ev.stack2args(1)
  def GET( self, A ):
    try:
      return [ self.symtable[A] ]
    except KeyError:
      raise RuntimeError('Unknown variable : Q'+str(A))
      
  @ev.stack2args(2)
  def LET( self, A, B ):
    self.symtable[A] = B
    return [ B ]
    
Evaluator = ev.Evaluator( [ArithmeticEvaluator( {} )] )