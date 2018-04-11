# Builder class that drives parser compilation
# Recursively traverses grammar tree and fetches compile methods from compiler
# for appropriate rules

class ParserBuilder:
  def __init__( self, compiler ):
    self._visited   = {}
    self.compiler  = compiler
    
  def __call__( self, target ):
    name = type(target).__name__
    
    if target in self._visited:
      return self._visited[target]  # Parser already built, return it
    else:
      if not hasattr( self.compiler, name ):
        raise RuntimeError("Compiler " + type(self.compiler).__name__ + " does not support building for type " + name )
    
    self._visited[target] = None  # recursion guard
    child_parsers = tuple( self( child ) for child in target ) # build children parsers
    
      # get attribute named as target class name from compiler
    compile = getattr( self.compiler, name )
      # call the builder compiler and pass target and child parsers as arguments
    parser = compile( target, child_parsers )
    
    self._visited[target] = parser  # Save 
    return parser