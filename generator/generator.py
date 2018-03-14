import task
from enum import EnumMeta
import task.visitors as vis
from task.visitor import Visitor, Visitable

def flatten(l):
  for el in l:
    if isinstance(el, list):
      yield from flatten(el)
    else:
      yield el

def lflatten(l):
  if isinstance(l, list ):
    return [x for x in flatten(l)]
  else:
    return l
        
def Parser( item ):
  if isinstance( item, Rule ):
    return item
  if isinstance( item, str ):
    return TerminalString( item )
  if isinstance( item, EnumMeta ):
    return Terminal( item )
  raise RuntimeError("Cannot use type " + type(item).__name__ + " in parser definition.")  

class Rule:
  def parse( self, lexer, handlers = {}, defaultHandler = flatten ):
    return vis.ParseVisitor(lexer, handlers, defaultHandler).visit(self)
    
  def accept( self, visitor ):
    return visitor.visit( self )
  
  def __or__( self, other ):
    return Alternative( [self, Parser(other)] )
    
  def __ror__( self, other ):
    return Alternative( [Parser(other), self] )
    
  def __and__( self, other ):
    return Sequence( [self, Parser(other)] )
    
  def __rand__( self, other ):
    return Sequence( [Parser(other), self] )
    
  def __rmul__( self, other ):
    return Sequence( [self for _ in range(other)] )
    
  def __pos__( self ):
    return Repeat( self )
  
  def __neg__( self ):
    return Not( self )
  
  def __invert__(self):
    return Optional(self)
  
  def __repr__( self ):
    return vis.ReprVisitor().visit(self)

@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Handle(Rule):
  def __init__( self, rule = None ):
    self.rule = rule

@Visitable( vis.ReprVisitor, vis.ParseVisitor )  
class Not(Rule):
  def __init__( self, rule ):
    self.rule = rule
  
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
  
  def __or__( self, other ):
    if isinstance(other, Alternative):
      return Alternative( self.options + other.options )
    return Alternative( self.options + [Parser(other)] )
  
  def __ror__( self, other ):
    if isinstance(other, Alternative):
      return Alternative( other.options + self.options )
    return Alternative( [Parser(other)] + self.options )

@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Sequence(Rule):
  def __init__( self, sequence ):
    self.sequence = sequence
    
  def __and__( self, other ):
    # if isinstance(other, Sequence):
    #   return Sequence( self.sequence + other.sequence )
    return Sequence( self.sequence + [Parser(other)] )
  
  def __rand__( self, other ):
    # if isinstance(other, Sequence):
    # `  return Sequence( other.sequence + self.sequence )
    return Sequence( [Parser(other)] + self.sequence )
    
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Repeat(Rule):
  def __init__( self, rule ):
    self.rule = rule
    
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Terminal(Rule):
  def __init__( self, handled):
    self.task = task.Task( handled )
    
_empty = lambda arg : []
  
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class TerminalString(Terminal):
  def __init__( self, regex):
    self.task = task.task.StringTask( regex )
    

@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Always(Rule):
  pass
  
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Never(Rule):
  pass
  
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Ignore(Rule):
  def __init__( self, rule ):
    self.rule = Parser(rule)