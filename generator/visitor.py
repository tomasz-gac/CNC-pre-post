class Visitable:
  def __init__( self, *classes ):
    self._classes = list(classes)
     
  def __call__( self, VisitableClass ):
    for VisitorClass in self._classes:
      if hasattr( VisitorClass, VisitableClass.__name__ ):
        method = getattr( VisitorClass, VisitableClass.__name__ )
        setattr( VisitableClass, VisitorClass.__name__, method )
      else:
        raise RuntimeError("Class " + VisitorClass.__name__ + " does not support visitation of type " + VisitableClass.__name__)
    return VisitableClass
    
class Visitor:
  def visit( self, visited, *args ):
    return getattr(type(visited), type(self).__name__ )( self, visited, *args )
  