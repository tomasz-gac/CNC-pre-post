# Injector class injects accept method to a given type
# Accept method implementation is yanked from method with name
# corresponding to target type name

class Injector:
  def __init__( self, injection ):
    self._visited   = set()
    self.injection  = injection
    
  def __call__( self, target, reinject = False ):
    method_name = 'accept'
    name = type(target).__name__
    
    if target in self._visited:
      return target
    else:
      if (not reinject) and hasattr( target, method_name ):
        raise RuntimeError("Object " + target.__repr__() + " has already injected with method " + method_name )
      if not hasattr( self.injection, name ):
        raise RuntimeError("Class " + type(self.injection).__name__ + " does not support injection for type " + name )
      self._visited.add(target)
      # get attribute named as target class name from injection
    method = getattr( self.injection, name )
      # call the method and pass target as argument
      # bind target to the result to create a bound method      
    injected_method = method(target).__get__(target, type(target))
      # set the bound method as target's method_name
    setattr( target, method_name, injected_method )

    for child in target:
      self( child, reinject )
    return target