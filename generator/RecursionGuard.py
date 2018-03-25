class RecursionGuard:
  def __init__(self, visited = set()):
    self.visited = visited
  def __call__( self, visited ):
    if visited in self.visited:
      return True
    else:
      self.visited.add( visited )
      return False
