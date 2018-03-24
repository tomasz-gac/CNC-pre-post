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
  
  def __repr__( self ):
    return vis.ReprVisitor().visit(self)
    
  def __getitem__( self, handle ):
    return Transform( self, handle )
      
@Visitable( vis.ReprVisitor, vis.Parser )
class Transform(Rule):
  def __init__( self, rule, handle = None ):
    if handle is None:
        self.handle = self
    self.rule = rule
    self.handle = handle
    super().__init__()
  
@Visitable( vis.ReprVisitor, vis.Parser )
class Handle(Rule):
  def __init__( self, rule = None ):
    self.rule = rule
    super().__init__()
  
@Visitable( vis.ReprVisitor, vis.Parser )  
class Not(Rule):
  def __init__( self, rule ):
    self.rule = rule
    super().__init__()
  
  def __neg__( self ):
    return self.rule
    
@Visitable( vis.ReprVisitor, vis.Parser )
class Optional(Rule):
  def __init__( self, rule ):
    self.rule = rule

@Visitable( vis.ReprVisitor, vis.Parser )
class Alternative(Rule):
  def __init__( self, options ):
    self.options = options
    super().__init__()
    
  def __or__( self, other ):
    if isinstance(other, Alternative):
      return Alternative( self.options + other.options )
    return Alternative( self.options + [make(other)] )
  
  def __ror__( self, other ):
    if isinstance(other, Alternative):
      return Alternative( other.options + self.options )
    return Alternative( [make(other)] + self.options )

@Visitable( vis.ReprVisitor, vis.Parser )
class Sequence(Rule):
  def __init__( self, sequence ):
    self.sequence = sequence
    super().__init__()
    
  '''def __and__( self, other ):
    return Sequence( self.sequence + [make(other)] )
  
  def __rand__( self, other ):
    return Sequence( [make(other)] + self.sequence )'''
    
  def __and__( self, other ):
    if isinstance(other, Sequence):
      return Sequence( self.sequence + other.sequence )
    return Sequence( self.sequence + [make(other)] )
  
  def __rand__( self, other ):
    if isinstance(other, Sequence):
      return Sequence( other.sequence + self.sequence )
    return Sequence( [make(other)] + self.sequence )

    
@Visitable( vis.ReprVisitor, vis.Parser )
class Repeat(Rule):
  def __init__( self, rule ):
    self.rule = rule
    super().__init__()
    
@Visitable( vis.ReprVisitor, vis.Parser )
class Terminal(Rule):
  def __init__( self, handle ):
    self.handle = self if handle is None else handle
    # self.task = handled
    super().__init__()