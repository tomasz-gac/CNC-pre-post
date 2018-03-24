from CNC.language import Arithmetic as cmd
import expression2 as expr
import generator as gen

class Evaluator:
  __slots__ = '_dispatch', '_symtable'
  def __init__( self ):
    self._dispatch = {
    cmd.ADD  : self.ADD, 
    cmd.SUB  : self.SUB, 
    cmd.MUL  : self.MUL, 
    cmd.DIV  : self.DIV, 
    cmd.POW  : self.POW, 
    cmd.LET  : self.LET,
    cmd.SETQ : self.SETQ,
    cmd.GETQ : self.GETQ
    }
    self._symtable = {}
  
  def ADD( self, stack ):
    stack[-2] = stack[-2] + stack[-1]
    del stack[-1]
  
  def SUB( self, stack ):
    stack[-2] = stack[-2] - stack[-1]
    del stack[-1]
    
  def MUL( self, stack ):
    print( str(stack[-2]) + '*' + str(stack[-1] ))
    stack[-2] = stack[-2] * stack[-1]
  
  def DIV( self, stack ):
    stack[-2] = stack[-2] / stack[-1]
    del stack[-1]
  
  def POW( self, stack ):
    stack[-2] = stack[-2] ** stack[-1]
    del stack[-1]
  
  def LET( self, stack ):
    self._symtable[stack[-2]] = stack[-1]
    stack[-2] = stack[-1]
    del stack[-1]
  
  def SETQ( self, stack ):
    pass
    
  def GETQ( self, stack ):
    stack[-1] = self._symtable[stack[-1]]
  
  def __call__( self, expression ):
    stack = []
    for symbol in expression:
      if isinstance( symbol, ( float, int ) ):
        stack.append(symbol)
      else:
        self._dispatch[ symbol ]( stack )
    if len(stack) != 1:
      raise RuntimeError('Invalid stack provided for evaluation')
    return stack[0]
    
ev = Evaluator()