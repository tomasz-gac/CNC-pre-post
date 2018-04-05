from generator.ReprVisitor import ReprVisitor
import copy
    
def make( item ):
  if isinstance( item, Rule ):
    return item
  return Terminal( item )

class Rule:
  def __or__( self, rhs ):
    if isinstance( rhs, tuple ):
      return Alternative( (self,) + tuple( make(rule) for rule in rhs ) )
    else:
      return Alternative( (self, make(rhs)) )
    
  def __ror__( self, lhs ):
    if isinstance( lhs, tuple ):
      return Alternative( tuple( make(rule) for rule in lhs ) + (self,) )
    else:
      return Alternative( (make(lhs), self) )
    
  def __and__( self, rhs ):
    if isinstance( rhs, tuple ):
      return Sequence( (self,) + tuple( make(rule) for rule in rhs ) )
    else:
      return Sequence( (self, make(rhs)) )
    
  def __rand__( self, lhs ):
    if isinstance( lhs, tuple ):
      return Sequence( tuple( make(rule) for rule in lhs ) + (self,) )
    else:
      return Sequence( (make(lhs), self) )
    
  def __rmul__( self, other ):
    return Sequence( tuple(self for _ in range(other)) )
    
  def __pos__( self ):
    return Repeat( self )
  
  def __neg__( self ):
    return Not( self )
  
  def __invert__(self):
    return Optional( self )
  
  def push( self, output = 'output' ):
    return Push(self, output)
    
  def pull( self, output = 'output' ):
    return Pull(self, output)
    
  def __iter__( self ):
    raise NotImplementedException()
    
  def __len__( self ):
    raise NotImplementedException()
  
  def __str__( self ):
   return self.__repr__() + (ReprVisitor().visit(self, True))
      
class Unary(Rule):
  def __init__(self, rule):
    self.rule = rule
    super().__init__()
      
  def __iter__( self ):    
    return iter( [ self.rule ] )
    
  def __len__( self ):
    return 1
  
class Nary(Rule):
  def __init__(self, rules ):
    self.rules = rules
    super().__init__()
    
  def __iter__( self ):    
    return iter( self.rules )
  
  def __len__( self ):
    return len(self.rules)
  
class Terminal(Rule):
  def __init__( self, handle ):
    self.handle = handle
    super().__init__()
    
  def __iter__( self ):
    return iter(())
  
  def __len__( self ):
    return 0


class Handle(Unary):
  def __init__( self, rule = None ):
    super().__init__(rule)
  
class Not(Rule):
  def __init__( self, rule ):
    super().__init__(rule)
  
  def __neg__( self ):
    return self.rule
    
class Optional(Unary):
  def __init__( self, rule ):
    super().__init__(rule)

class Alternative(Nary):
  def __init__( self, rules ):
    super().__init__(rules)
    
  def __or__( self, other ):
      # Parantheses are not important
    self.rules += make(other),
    return self
  
  def __ror__( self, other ):
      # Parantheses are not important
    self.rules = (make(other),) + self.rules
    return self

class Sequence(Nary):
  def __init__( self, rules ):
    super().__init__( rules )
    
  def __and__( self, other ):
      # makes sure that parantheses are preserved
    if isinstance( other, Sequence ):
      return Sequence( (self, other) )
    else:
      return Sequence( self.rules + (make(other),) )
  
  def __rand__( self, other ):
      # makes sure that parantheses are preserved
    if isinstance( other, Sequence ):
      return Sequence( (other, self) )
    else:
      return Sequence( (make(other),) + self.rules )

class Repeat(Unary):
  def __init__( self, rule ):
    super().__init__(rule)

class Push(Unary):
  def __init__( self, rule, output ):
    self.output = output
    super().__init__(rule)
    
class Pull(Unary):
  def __init__( self, rule, output ):
    self.output = output
    super().__init__(rule)