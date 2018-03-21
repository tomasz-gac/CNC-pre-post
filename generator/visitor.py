class Visitable:
  def __init__( self, *classes ):
    self._classes = list(classes)
     
  def __call__( self, VisitableClass ):
    '''for cls in self._classes:
      if hasattr( cls, decoratedClass.__name__ ):
        method = getattr( cls, decoratedClass.__name__ )
        if not hasattr( cls, "_visitor_dispatch" ):
          cls._visitor_dispatch = {}
        cls._visitor_dispatch[ decoratedClass ] = method
      else:
        raise RuntimeError("Class " + cls.__name__ + " does not support visitation of type " + decoratedClass.__name__)'''
    for VisitorClass in self._classes:
      if hasattr( VisitorClass, VisitableClass.__name__ ):
        method = getattr( VisitorClass, VisitableClass.__name__ )
        setattr( VisitableClass, VisitorClass.__name__, method )
      else:
        raise RuntimeError("Class " + VisitorClass.__name__ + " does not support visitation of type " + VisitableClass.__name__)
      # lambda self, visitor, *args : getattr(visitor, decoratedClass.__name__)( self, *args ) )
    return VisitableClass
    
  
def _visitor_dispatch( self, object, *args, **kwargs ):
  return type(self)._dispatch[ type(object) ]( self, object, *args, **kwargs )
        
class Visitor:
  pass
  '''def visit( self, object, *args ):
    # result = type(self)._visitor_dispatch[ type(object) ]( self, object, *args )
    return object.accept( self, *args ) 
    # return object.accept( self, *args, **kwargs )'''
  
  