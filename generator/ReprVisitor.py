from generator.RecursionGuard import RecursionGuard

class ReprVisitor:
  def __init__(self):
    # self._depth = 0
    self.identTable = ['+']
    self.visited = []
    self._depth = 0
    
  def visit( self, rule, last ):
    self._depth += 1
    self.identTable[-1] = '+'
    result = '\n' + "".join(self.identTable)
    self.identTable[self._depth-1] = ' ' if last else '|'
    
    self.identTable.append('+')
    if rule in self.visited:
      result += "<<Rule "+str(self.visited.index(rule)+1)+':'+self.getname(rule)+ " recursion>>"
    else:
      self.visited.append(rule)
      result += str(len(self.visited)) + ":" + self.get_repr( rule )
    self._depth -= 1
    del self.identTable[-1]
    return result
    
  def get_repr( self, rule ):
    s = self.getname(rule)
      # also works for terminals
      # zip of lists with different lengths terminates at len(shorter list)
    lst = ([False] * (len(rule)-1)) + [True] # (at least one element)
    s += ''.join( ( self.visit(child, last ) for (child, last) in zip( rule, lst ) ) )
    return s
    
  def getname( self, rule ):
    try:
      name = type(rule).__name__ + ' (' + rule.handle + ')'
    except AttributeError:
      try:
        name = type(rule).__name__ + ' (' + rule.name + ')'
      except AttributeError:
        name = type(rule).__name__
    return name
  