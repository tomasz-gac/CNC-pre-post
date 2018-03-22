import generator
import generator.visitors as vis
from generator.visitor import Visitor, Visitable
import copy
    
def make( item ):
  if isinstance( item, Rule ):
    return item
  '''if isinstance( item, str ):
    return TerminalString( item )
  if isinstance( item, EnumMeta ):
    return Terminal( generator.Task(item) )
  return Terminal( generator.HandledTask(item) )'''
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
    
def lexerEmpty( _, __, lexer ):
  return not lexer.hasInput()

def _flatten(l):
  for el in l:
    if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes, dict, set)):
      yield from flatten(el)
    else:
      yield el

def flatten( l ):
  if isinstance(l, collections.Iterable) and not isinstance( l, (dict, set) ):
    return _flatten(l)
  else:
    return l
    
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Parser(Rule):
  def __init__( self, rule, terminals, transforms ):
    self.rule = rule
    self.transforms = transforms
    self.terminals = terminals
    super().__init__()
    
  def __call__( self, lexer, input = None ):
    if input is not None:
      lexer.set(input)
    visitor = vis.ParseVisitor( lexer, self.terminals, self.transforms )
    self.state = visitor.state
    return self.rule.ParseVisitor( visitor )
  
    
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Transform(Rule):
  def __init__( self, rule, handle = None ):
    if handle is None:
        self.handle = self
    self.rule = rule
    self.handle = handle
    super().__init__()
  
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Handle(Rule):
  def __init__( self, rule = None ):
    self.rule = rule
    super().__init__()
  
@Visitable( vis.ReprVisitor, vis.ParseVisitor )  
class Not(Rule):
  def __init__( self, rule ):
    self.rule = rule
    super().__init__()
  
  def __neg__( self ):
    return self.rule
    
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Optional(Rule):
  def __init__( self, rule ):
    self.rule = rule

@Visitable( vis.ReprVisitor, vis.ParseVisitor )
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

@Visitable( vis.ReprVisitor, vis.ParseVisitor )
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

    
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Repeat(Rule):
  def __init__( self, rule ):
    self.rule = rule
    super().__init__()
    
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Terminal(Rule):
  def __init__( self, handle ):
    self.handle = self if handle is None else handle
    # self.task = handled
    super().__init__()