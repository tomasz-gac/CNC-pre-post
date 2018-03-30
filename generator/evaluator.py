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
  
def _append( symbol, stack ):
  stack.append(symbol)
    
class Evaluator:
  def __init__( self, evaluators ):
    self.evaluators = { evaluator.enum : evaluator for evaluator in evaluators }
    if len(self.evaluators) < len(evaluators):
      raise RuntimeError('Multiple handlers provided for Evaluator handle the same Enum type')
    values = []
    for evaluator in evaluators:
      values += [ item.value for item in list(type(evaluator).enum) ]
    if len(values) != len(set(values)):
      raise RuntimeError('Enum values of handlers provided for Evaluator are not unique')
     
  def __call__( self, expression ):
    stack = []
    for symbol in expression:
      self.evaluators.get( type(symbol), _append )( symbol, stack )
    return stack
    
  def __getitem__(self, item):
    return self.evaluators[item]