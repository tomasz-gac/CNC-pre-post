from generator.RecursionGuard import RecursionGuard

class ReprVisitor:
  def __init__(self):
    self._depth = 0
    self.visited = []
    
  def visit( self, rule ):
    self._depth += 1
    result = self._ident()
    if rule in self.visited:
      result += "<<Rule "+str(self.visited.index(rule)+1)+ " recursion>>"
    else:
      self.visited.append(rule)
      result += str(len(self.visited)) + ":" + self.get_repr( rule )
    self._depth -= 1
    return result
    
  def _ident( self ):
    s = '\n' + "|".join(["" for _ in range(self._depth)])
    return s
    
  def get_repr( self, rule ):
    try:
      name = type(rule).__name__ + '(' + rule.handle + ')'
    except AttributeError:
      try:
        name = type(rule).__name__ + '(' + rule.name + ')'
      except AttributeError:
        name = type(rule).__name__
    s = name
    s += "".join( ( self.visit(child) for child in rule) )    
    # s += self._ident() if len(rule) > 0 else ''
    return s