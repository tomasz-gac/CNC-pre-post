import generator
from enum import EnumMeta
import generator.visitors as vis
from generator.visitor import Visitor, Visitable
import collections
    
def make( item ):
  if isinstance( item, Rule ):
    return item
  if isinstance( item, str ):
    return TerminalString( item )
  if isinstance( item, EnumMeta ):
    return Terminal( item )
  raise RuntimeError("Cannot use type " + type(item).__name__ + " in parser definition.")  

class Rule:
  def accept( self, visitor ):
    return visitor.visit( self )
  
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
  def __init__( self, rule, handlers = {}, defaultHandler = lambda x : x ):
    self.rule = rule
    self.handlers = handlers
    self.defaultHandler = defaultHandler
    
  def __call__( self, lexer, input = None ):
    if input is not None:
      lexer.set(input)
    visitor = vis.ParseVisitor( lexer, self.handlers, self.defaultHandler )
    result = visitor.visit( self.rule )
    return result, visitor.result
    
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
  
  '''def __or__( self, other ):
    if isinstance(other, Alternative):
      return Alternative( self.options + other.options )
    return Alternative( self.options + [make(other)] )
  
  def __ror__( self, other ):
    if isinstance(other, Alternative):
      return Alternative( other.options + self.options )
    return Alternative( [make(other)] + self.options )'''

@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Sequence(Rule):
  def __init__( self, sequence ):
    self.sequence = sequence
    
  '''def __and__( self, other ):
    return Sequence( self.sequence + [make(other)] )
  
  def __rand__( self, other ):
    return Sequence( [make(other)] + self.sequence )'''
    
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Repeat(Rule):
  def __init__( self, rule ):
    self.rule = rule
    
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Terminal(Rule):
  def __init__( self, handled):
    self.task = generator.Task( handled )
    
_empty = lambda arg : []
  
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class TerminalString(Terminal):
  def __init__( self, regex):
    self.task = generator.task.StringTask( regex )
    

@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Always(Rule):
  pass
  
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Never(Rule):
  pass
  
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Ignore(Rule):
  def __init__( self, rule ):
    self.rule = make(rule)
    
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Bracket(Rule):
  def __init__(self, rule):
    self.rule = make(rule)

@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Copy(Rule):
  def __init__(self, name, rule):
    self.name = name
    self.rule = make(rule)

@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Cut(Rule):
  def __init__(self, name, rule):
    self.name = name
    self.rule = make(rule)
    
@Visitable( vis.ReprVisitor, vis.ParseVisitor )
class Paste(Rule):
  def __init__(self, name):
    self.name = name
