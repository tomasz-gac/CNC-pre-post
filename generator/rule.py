import generator
import generator.visitors as vis
from generator.visitor import Visitor, Visitable
import copy
    
def make( item ):
  if isinstance( item, Rule ):
    return item
  return Terminal( item )
  
  # raise RuntimeError("Cannot use type " + type(item).__name__ + " in parser definition.")  

class Rule:
  def __or__( self, rhs ):
    if isinstance( rhs, list ):
      return Alternative( [self] + [ make(x) for x in rhs ] )
    else:
      return Alternative( [self, make(rhs)] )
    
  def __ror__( self, lhs ):
    if isinstance( lhs, list ):
      return Alternative( [ make(x) for x in lhs ] + [self] )
    else:
      return Alternative( [make(lhs), self] )
    
  def __and__( self, rhs ):
    if isinstance( rhs, list ):
      return Sequence( [self] + [ make(x) for x in rhs ] )
    else:
      return Sequence( [self, make(rhs)] )
    
  def __rand__( self, lhs ):
    if isinstance( lhs, list ):
      return Sequence( [ make(x) for x in lhs ] + [self] )
    else:
      return Sequence( [make(lhs), self] )
    
  def __rmul__( self, other ):
    return Sequence( [self for _ in range(other)] )
    
  def __pos__( self ):
    return Repeat( self )
  
  def __neg__( self ):
    return Not( self )
  
  def __invert__(self):
    return Optional( self )
  
  # def __repr__( self ):
  #  return vis.ReprVisitor().visit(self)
    
  # def __getitem__( self, handle ):
  #  return Transform( self, handle )
    
  def push( self ):
    return Push(self)
    
  def pull( self ):
    return Pull(self)
      
class Unary(Rule):
  def __init__(self, rule):
    self.rule = rule
    super().__init__()
      
  def visit_children( self, visitor ):    
    visitor( self.rule )
  
class Nary(Rule):
  def __init__(self, rules ):
    self.rules = rules
    super().__init__()
    
  def visit_children( self, visitor ):    
    for rule in self.rules:
      visitor( rule )
  
@Visitable( vis.ReprVisitor )
class Terminal(Rule):
  def __init__( self, handle ):
    self.handle = self if handle is None else handle
    super().__init__()
    
  def visit_children( self, visitor ):
    pass
  
'''@Visitable( vis.ReprVisitor )
class Transform(Unary):
  def __init__( self, rule, handle = None ):
    if handle is None:
        self.handle = self
    self.handle = handle
    super().__init__(rule)'''
  
@Visitable( vis.ReprVisitor )
class Handle(Unary):
  def __init__( self, rule = None ):
    super().__init__(rule)
  
@Visitable( vis.ReprVisitor )  
class Not(Rule):
  def __init__( self, rule ):
    super().__init__(rule)
  
  def __neg__( self ):
    return self.rule
    
@Visitable( vis.ReprVisitor )
class Optional(Unary):
  def __init__( self, rule ):
    super().__init__(rule)

@Visitable( vis.ReprVisitor )
class Alternative(Nary):
  def __init__( self, rules ):
    super().__init__(rules)
    
  def __or__( self, other ):
    if isinstance(other, Alternative):
      return Alternative( self.rules + other.rules )
    return Alternative( self.rules + [make(other)] )
  
  def __ror__( self, other ):
    if isinstance(other, Alternative):
      return Alternative( other.rules + self.rules )
    return Alternative( [make(other)] + self.rules )

@Visitable( vis.ReprVisitor )
class Sequence(Nary):
  def __init__( self, rules ):
    super().__init__( rules )
    
  def __and__( self, other ):
    if isinstance(other, Sequence):
      return Sequence( self.rules + other.rules )
    return Sequence( self.rules + [make(other)] )
  
  def __rand__( self, other ):
    if isinstance(other, Sequence):
      return Sequence( other.rules + self.rules )
    return Sequence( [make(other)] + self.rules )

    
@Visitable( vis.ReprVisitor )
class Repeat(Unary):
  def __init__( self, rule ):
    super().__init__(rule)

class Push(Unary):
  def __init__( self, rule ):
    super().__init__(rule)
    
class Pull(Unary):
  def __init__( self, rule ):
    super().__init__(rule)