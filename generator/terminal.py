import re
from enum import EnumMeta
from copy import copy, deepcopy
from generator.injector import Injector
    
class TerminalBase:
  def ignore( self, returned = [] ):
    return Ignore( self, returned )
    
  def __rshift__( self, wrapper ):
    return Wrapper( self, wrapper )
    
def make( t ):
  if isinstance( t, TerminalBase ):
    return t
  if isinstance( t, EnumMeta ):
    return Task( t )
  if isinstance( t, str ):
    return StringTask( t )
  if isinstance( t, dict ):
    return { key : make(value) for (key,value) in t.items() }
  return TaskHandler( t )

class ParserFailedException( Exception ):
  pass

def make_parser( State ):
  class Parser(TerminalBase):
    __slots__ = 'rule'
    def __init__( self, rule, compiler, recompile = False ):
      self.rule = Injector(compiler)( deepcopy( rule ), recompile )
    
    def __call__( self, input ):
      state = State( input )
      result = self.rule.accept( self.rule, state )
      return result, state.input
  return Parser

class StringState:
  __slots__ = 'rule', 'stack', 'preprocess', '__input'
  def __init__( self, input ):
    self.stack = []
    self.__input = input    
  
    # reimplementation of __init__ without injection and deepcopying
    # One can call _fork only on initialized objects
  def fork( self ):
    frk = StringState.__new__(StringState)
    frk.stack = self.stack[:]
    frk.__input = self.__input[:]
    return frk
  
  def join( self, frk ):
    self.stack = frk.stack
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

class Wrapper(TerminalBase):
  def __init__( self, wrapped, wrapper ):
    self.wrapped = wrapped
    self.wrapper = wrapper
    
  def __call__( self, line ):
    result, rest = self.wrapped( line )
    return self.wrapper( result ), rest

def group( f, number = 0 ):
  def impl( token ):
    return [ f( token[0].groups[number] ) ]
  return impl

def get( descriptor ):
  def impl( token ):
    return [ descriptor.__get__( token[0] ) ]
  return impl

  # Class accepting an Enum with values treated as regex
  # __call__ accepts a string and fills the Task.match and type of matched Enum
class Task(TerminalBase):
  __slots__ = "_typeEnum", "groups", "type", "line", "match", "_re"
  def __init__( self, typeEnum ):
    self.setPattern( typeEnum )

  def setPattern( self, typeEnum ):
      #clear state variables
    self._typeEnum = typeEnum
    self.match = None
    self.groups = None
    self.type = None
      #set the regex lookup dict
    self._re = { taskType : re.compile(taskType.value) for taskType in self._typeEnum }
  
    # no deep copying regexes. Members must be immutable
  def __deepcopy__( self, memo ):
    return copy(self)
  
  def __call__( self, line ):
    self.line = line   
    self.type = None
    
    for taskType, re in self._re.items():
      match = re.match(line)
      if match is not None:
        self.match = match.group()
        self.groups = match.groups()
        self.type = taskType
        return [ self ], match.string[match.end(0):]
    
    raise ParserFailedException()
    
  def __repr__( self ):
    return ( "<Task"
      + ((" : "+str(self.match)) if self.match else "")
      + ((" type: "+str(self.type)) if self.type else "")
      # + ((" groups: "+str(self.groups)) if self.groups else "")
      + ">" )

  # Class that maps terminals to pre-defined lookup values
  # Requires terminal to return a list with a single value
class Lookup(TerminalBase):
  def __init__( self, terminal, table ):
    self.terminal = make(terminal)
    self.table = table
    
  def __call__( self, line ):
    result, rest = self.terminal( line )
    return self.table[ result[0].type ], rest

def make_lookup( table ):
  def impl( terminal ):
    return Lookup( terminal, table )
  return impl

      
  # Simple regex task    
class StringTask(Task):
  def __init__(self, rex ):
    super().__init__( rex )
    
  def setPattern( self, rex ):
      #clear state variables
    self._typeEnum = rex
    self.groups = None
    self.type = None
      #set the regex lookup list
    self._re = { None : re.compile(rex) }

def _doHandle( self, task ):
  return type(self)._dispatch[task.type]( self, task )

  # Class decorator that maps enum values to functions with matching names
  # Handler.__call__ becomes a dispatch function
class Handler:  
  def __init__( self, Task ):
    self.tasks = Task
  def __call__( self, Handler ):
    Handler.enum = self.tasks
    Handler._dispatch = ( #find all handlers
      { self.tasks[name] : getattr(Handler, name) for name in  # all atributes
        (  
          handler for handler in #all callable attributes
            ( method for method in dir(Handler) if callable(getattr(Handler, method)) )
          if handler in ( x.name for x in list(self.tasks) ) #if they share name with Task enum values
        )
      }
    )
    if( len(self.tasks) != len(Handler._dispatch) ):
      raise Exception( "Not all task types handled by "+str(Handler) )
      #set the handling method in Handler
    Handler.__call__ = _doHandle
    Handler.handled = self.tasks
    return Handler

    
  # Terminal that creates a Task
  # and links it to a class decorated with @Handler
  # returns result of the handler.
class TaskHandler(Task):
  def __init__( self, handler ):
    self.handler = handler
    super().__init__( handler.enum )
    
  def __call__( self, line ):
    result, rest = Task.__call__( self, line )
    return self.handler( result ), rest