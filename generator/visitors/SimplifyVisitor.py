import generator.visitor as vis

def simplify( r ):
  v = RecursiveVisitor()
  v.visit(r)
  s = SimplifyVisitor( v.recursive )
  s.visit(r)

class SimplifyVisitor(vis.Visitor):
  def __init__( self, recursive ):
    self.recursive = recursive
    self.visited = set()

  def _visit( self, visited ):
    if visited not in self.recursive:
      self.visit( visited )      
    
  def Parser( self, visited ):
    self._visit( visited.rule )
  
  def Handle( self, visited ):
    self._visit( visited.rule )
    
  def Not( self, visited ):
    self._visit( visited.rule )
    
  def Optional( self, visited ):
    self._visit( visited.rule )
    
  def Alternative( self, visited ):
    visited.options = list( generator.rule._flatten([ 
      x if not isinstance(x, generator.rule.Alternative) or x in self.recursive else x.options 
      for x in visited.options 
    ])
    )
    for rule in visited.options:
      self._visit( rule )
    
    
  def Sequence( self, visited ):
    visited.sequence = list( generator.rule._flatten([ 
      x if not isinstance(x, generator.rule.Sequence) or x in self.recursive else x.sequence
      for x in visited.sequence 
    ])
    )
    for rule in visited.sequence:
      self._visit( rule )
    
  def Repeat( self, visited ):
    self._visit( visited.rule )
      
  def Terminal( self, visited):
    pass
  
  def TerminalString( self, visited ):
    pass
    
  def Always( self, visited ):
    pass
  
  def Never( self, visited ):
    pass
    
  def Ignore( self, visited ):
    self._visit( visited.rule )


class RecursiveVisitor(vis.Visitor):
  def __init__( self ):
    self.visited    = set()
    self.recursive  = set()

  def _checkRecursive( self, visited ):
    if visited in self.visited:
      self.recursive.add( visited )
      return True
    else:
      self.visited.add( visited )
      return False
    
  def Parser( self, visited ):
    if not self._checkRecursive( visited ):
      self.visit( visited.rule )    
  
  def Handle( self, visited ):
    if not self._checkRecursive( visited ):
      self.visit( visited.rule )
    
  def Not( self, visited ):
    if not self._checkRecursive( visited ):
      self.visit( visited.rule )
    
  def Optional( self, visited ):
    if not self._checkRecursive( visited ):
      self.visit( visited.rule )
    
  def Alternative( self, visited ):
    if not self._checkRecursive( visited ):
      for rule in visited.options:
        self.visit( rule )
    
  def Sequence( self, visited ):
    if not self._checkRecursive( visited ):
      for rule in visited.sequence:
        self.visit( rule )
    
  def Repeat( self, visited ):
    if not self._checkRecursive( visited ):
      self.visit( visited.rule )
      
  def Terminal( self, visited):
    self._checkRecursive( visited )
  
  def TerminalString( self, visited ):
    self._checkRecursive( visited )
    
  def Always( self, visited ):
    self._checkRecursive( visited )
  
  def Never( self, visited ):
    self._checkRecursive( visited )
    
  def Ignore( self, visited ):
    if not self._checkRecursive( visited ):
      self.visit( visited.rule )

import generator.rule