class ReprVisitor:
  def __init__(self):
    self.identTable = ['+'] # so that we can use identTable[-1]
    self.visited = []
    
  def visit( self, rule, islast ):
    result = self.ident( islast ) # insert identiation
    if rule in self.visited:
      result += "->"+str(self.visited.index(rule)+1)+':'+self.getname(rule)
    else:
      self.visited.append(rule)
      result += str(len(self.visited)) + ":" + self.get_repr( rule )
    del self.identTable[-1] # remove identiation
    return result
    
  def ident( self, last ):
    self.identTable[-1] = '+'                   # change to split
    result = '\n' + "".join(self.identTable)    # print ident
      # if last element stop printing in next
    self.identTable[-1] = ' ' if last else '|'
    self.identTable.append('+')                 # more identiation
    return result
  
  def get_repr( self, rule ):
    if rule is None:
      return 'None'
    s = self.getname(rule)
      # also works for terminals
      # zip of lists with different lengths terminates at len(shorter list)
    lst = ([False] * (len(rule)-1)) + [True] # (at least one element)
    s += ''.join( ( self.visit(child, last ) for (child, last) in zip( rule, lst ) ) )
    return s
    
  def getname( self, rule ):
    try:
      name = type(rule).__name__ + ' (' + rule.name + ')'
    except AttributeError:
      name = type(rule).__name__
    return name
  