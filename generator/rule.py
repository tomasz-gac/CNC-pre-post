from generator.ReprVisitor import ReprVisitor
from generator.ParserBuilder import ParserBuilder
import copy
   
class Rule:    
  def __iter__( self ):
    raise NotImplementedException()
    
  def __len__( self ):
    raise NotImplementedException()
  
  def __str__( self ):
   return self.__repr__() + (ReprVisitor().visit(self, True))
   
  def compile( self, compiler ):
    builder = ParserBuilder( compiler )
    return builder( self )
      
class Unary(Rule):
  __slots__ = '_rule'
  def __init__(self, rule):
    self._rule = rule
    super().__init__()
    
  @property
  def rule( self ):
    return self._rule
  
  @rule.setter
  def rule( self, value ):
    self._rule = value
      
  def __iter__( self ):    
    return iter( [ self.rule ] )
    
  def __len__( self ):
    return 1
  
class Nary(Rule):
  __slots__ = '_rules'
  def __init__(self, *rules ):
    self._rules = rules
    super().__init__()
    
  @property
  def rules( self ):
    return self._rules
  
  @rules.setter
  def rules( self, value ):
    self._rules = value
  
  def __iter__( self ):    
    return iter( self.rules )
  
  def __len__( self ):
    return len(self.rules)
  
class Terminal(Rule):
  def __init__( self, name = None ):
    self.name = name
    super().__init__()
    
  def __iter__( self ):
    return iter(())
  
  def __len__( self ):
    return 0

class Handle(Unary):
  def __init__( self, rule = None ):
    super().__init__(rule)
  
class Not(Rule):  
  def __neg__( self ):
    return self.rule
    
class Optional(Unary):
  pass

class Alternative(Nary):    
  pass

class Sequence(Nary):    
  pass
  
class Repeat(Unary):
  pass

class Push(Unary):
  pass 