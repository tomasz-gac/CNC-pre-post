import re
from copy import copy, deepcopy
from generator.injector import Injector
    
class TerminalBase:
  def ignore( self, returned = [] ):
    return Ignore( self, returned )
    
  def __rshift__( self, wrapper ):
    return Wrapper( self, wrapper )
    return Wrapper( self, wrapper )
    
def make( t ):
  if isinstance( t, TerminalBase ):
    return t
  if isinstance( t, dict ):
    return Pattern( t )

class ParserFailedException( Exception ):
  def __init__( self, string ):
    super().__init__(string)

def make_parser( State ):
  class Parser(TerminalBase):
    __slots__ = 'rule'
    def __init__( self, rule, compiler, recompile = False ):
      self.rule = Injector(compiler)( deepcopy( rule ), recompile )
    
    def __call__( self, input ):
      state = State( input )
      result = self.rule.accept( self.rule, state )
      if len(result) > 0:
        raise RuntimeError('Parser returned with fallthrough: ' + str(result) )
      return state.Return(), state.input
  return Parser

class StringState:
  __slots__ = 'rule', 'stack', 'symtable', 'preprocess', '__input'
  def __init__( self, input ):
    self.stack = []
    self.symtable = {}
    self.__input = input    
  
  def __call__( self, result ):
    for f in result:
      f( self )
    return []
    
  def Return( self ):
    return self.stack
    
  def fork( self ):
    frk = StringState.__new__(StringState)
    frk.stack = self.stack[:]
    frk.symtable = dict(self.symtable)
    frk.__input = self.__input[:]
    return frk
  
  def join( self, frk ):
    self.stack = frk.stack
    self.symtable = frk.symtable
    self.__input = frk.__input
    
  @property
  def input( self ):
    return self.__input
    
  @input.setter
  def input( self, line ):
    self.__input = line.lstrip(' ')

StrParser = make_parser(StringState)
  
class Ignore(TerminalBase):
  def __init__( self, task, returned = [] ):
    self.task = make(task)
    self.returned = returned
  def __call__( self, line ):
    result, rest = self.task(line)
    return self.returned, rest

class Return(TerminalBase):
  def __init__( self, returned ):
    self.returned = returned
  def __call__( self, line ):
    return self.returned, line


class ret(TerminalBase):
  def __init__( self, *args ):
    self.returned = list(args)
    
  def __call__( self, *args ):
    return self.returned
  
class Wrapper(TerminalBase):
  def __init__( self, wrapped, wrapper ):
    self.wrapped = wrapped
    self.wrapper = wrapper
    
  def __call__( self, line ):
    result, rest = self.wrapped( line )
    return self.wrapper( result ), rest

class Pattern(TerminalBase):
  def __init__( self, lookup ):
    self._lookup = { re.compile( pattern ) : callback for (pattern, callback ) in lookup.items() }
    
  def __deepcopy__( self, memo ):
    return copy( self )
    
  def __call__( self, line ):
    for re,callback in self._lookup.items():
      match = re.match( line )
      if match is not None:
        return callback( match ), match.string[match.end(0):]
    
    raise ParserFailedException('Pattern exhausted with no matches')