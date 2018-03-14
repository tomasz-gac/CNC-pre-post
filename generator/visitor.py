class Visitable:
  def __init__( self, *classes ):
    self._classes = list(classes)
    
  def __call__( self, decoratedClass ):
    for cls in self._classes:
      if hasattr( cls, decoratedClass.__name__ ):
        method = getattr( cls, decoratedClass.__name__ )
        if not hasattr( cls, "_visitor_dispatch" ):
          cls._visitor_dispatch = {}
        cls._visitor_dispatch[ decoratedClass ] = method
      else:
        raise RuntimeError("Class " + cls.__name__ + " does not support visitation of type " + decoratedClass.__name__)
    return decoratedClass

def _visitor_dispatch( self, object, *args, **kwargs ):
  return type(self)._dispatch[ type(object) ]( self, object, *args, **kwargs )
        
class Visitor:
  def visit( self, object, *args, **kwargs ):
    # name = getattr(object, "name") if hasattr(object, "name") else str(type(object) )
    # print( "visiting " + name )
    result = type(self)._visitor_dispatch[ type(object) ]( self, object, *args, **kwargs )
    # print( "leaving " + name )
    return result
  
  