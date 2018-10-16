import weakref

# Builder class that drives parser compilation
# Recursively traverses grammar tree and fetches compile methods from compiler
# for appropriate rules

class ParserBuilder:
  def __init__( self, compiler ):
    self.compiler  = compiler
      # rule -> parser mapping
      # None siginifies a recursive call to parent parser
    self._visited   = {}
    
  def __call__( self, target ):
    name = type(target).__name__
      
      # Test whether target has already been visited
    if target in self._visited:
      if self._visited[target] is None:
          # Parser has already been visited, but has not yet been built
          # Create a delayed redirection to be initialized after parent parser has been built
        self._visited[target] = Recursion()
      return self._visited[target]
    else:
      if not hasattr( self.compiler, name ):
        raise RuntimeError("Compiler " + type(self.compiler).__name__ + " does not support building of type " + name )
    
    self._visited[target] = None  # recursion guard - parser not yet built
    child_parsers = tuple( self( child ) for child in target ) # build children parsers
    
      # compile method is named after class it is supposed to compile
    compile = getattr( self.compiler, name )
    parser = compile( target, child_parsers )
          
    if self._visited[target] is None: # No children referencing this parser
      self._visited[target] = parser  # No recursion
    elif isinstance( self._visited[target], Recursion ):  # A child references this parser
      self._visited[target].target = weakref.proxy(parser)  # update the recursion target
    
    return parser
    
class Recursion:
  __slots__ = 'target'
  
  def __call__( self, state ):
    return self.target( state )
