from CNC.language import Arithmetic as cmd
import expression2 as expr
import generator as gen

def _handleEnum( self, task, *args ):
  return type(self)._dispatch[task]( self, *args )

  # Class decorator that maps enum values to functions with matching names
  # Handler.__call__ becomes a dispatch function
class Handler:  
  def __init__( self, EnumType ):
    self.EnumType = EnumType
  def __call__( self, Handler ):
    Handler.enum = self.EnumType
    Handler._dispatch = ( #find all handlers
      { self.EnumType[name] : getattr(Handler, name) for name in  # all atributes
        (  
          handler for handler in #all callable attributes
            ( method for method in dir(Handler) if callable(getattr(Handler, method)) )
          if handler in ( x.name for x in list(self.EnumType) ) #if they share name with Task enum values
        )
      }
    )
    if( len(self.EnumType) != len(Handler._dispatch) ):
      raise Exception( "Not all task types handled by "+str(Handler) )
      #set the handling method in Handler
    Handler.__call__ = _handleEnum
    Handler.handled = self.EnumType
    return Handler



class Evaluator:
  __slots__ = '_dispatch', '_symtable'
  def __init__( self ):
    self._symtable = {}
  
  @Handler( cmd )
  class CMDdispatcher:
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
      self._symtable[stack[-2]] = stack[-1]
      stack[-2] = stack[-1]
      del stack[-1]
    
    def SETQ( self, stack ):
      pass
      
    def GETQ( self, stack ):
      stack[-1] = self._symtable[stack[-1]]
      
    def SETREG( self, stack ):
      raise NotImplementedError()
  
  def __call__( self, expression ):
    stack = []
    dispatcher = Evaluator.CMDdispatcher()
    for symbol in expression:
      if isinstance( symbol, ( float, int ) ):
        stack.append(symbol)
      else:
        dispatcher( symbol, stack )
    if len(stack) != 1:
      raise RuntimeError('Invalid stack provided for evaluation. Result: ' + str(stack))
    return stack[0]
    
ev = Evaluator()