import generator.evaluator as ev
from expression.commands import Arithmetic

@ev.Handler( Arithmetic )
class ArithmeticEvaluator:
  def __init__( self, registers = {}, symtable = {} ):
    self.registers = registers
    self.symtable = symtable
    
  def ADD( self, stack ):
    stack[-2] = stack[-2] + stack[-1]
    del stack[-1]
  
  def SUB( self, stack ):
    stack[-2] = stack[-2] - stack[-1]
    del stack[-1]
    
  def MUL( self, stack ):
    stack[-2] = stack[-2] * stack[-1]
    del stack[-1]
  
  def DIV( self, stack ):
    stack[-2] = stack[-2] / stack[-1]
    del stack[-1]
  
  def POW( self, stack ):
    stack[-2] = stack[-2] ** stack[-1]
    del stack[-1]
  
  def LET( self, stack ):
    self.symtable[stack[-1]] = stack[-2]
    del stack[-1]
  
  def SETQ( self, stack ):
    pass
    
  def GETQ( self, stack ):
    try:
      stack[-1] = self.symtable[stack[-1]]
    except KeyError:
      raise RuntimeError('Unknown variable : Q'+str(stack[-1]))
    
  def SETREG( self, stack ):
    self.registers[stack[-1]] = stack[-2]
    del stack[-2:]
    
Evaluator = ev.Evaluator( [ArithmeticEvaluator()] )