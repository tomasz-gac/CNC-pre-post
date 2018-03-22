import re
import itertools
from enum import Enum, EnumMeta, unique
import copy
import generator as gen

def _doHandle( self, task ):
  return type(self)._dispatch[task.type]( self, task )

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
    
class TerminalBase:
  def ignore( self ):
    return Ignore(self)
    
  def __rshift__( self, wrapper ):
    return Wrapper( self, wrapper )
    
def make_terminal( t ):
  if isinstance( t, TerminalBase ):
    return t
  if isinstance( t, EnumMeta ):
    return gen.Task( t )
  if isinstance( t, str ):
    return gen.StringTask( t )
  return gen.TaskHandler( t )
  
def make_terminals( terminals ):
  return { key : make_terminal(value) for (key,value) in terminals.items() }

class Ignore(TerminalBase):
  def __init__( self, task ):
    self.task = make_terminal(task)
  def __call__( self, line ):
    result, rest = self.task(line)
    return None, rest
    #override for unnecessary wrapping
  def ignore( self ):
    return self

class Lookup(TerminalBase):
  def __init__( self, terminal, table ):
    self.terminal = make_terminal(terminal)
    self.table = table
    
  def __call__( self, line ):
    result, rest = self.terminal( line )
      # table has to handle None
    return self.table[ result.type ], rest

def makeLookup( table ):
  def impl( terminal ):
    return Lookup( terminal, table )
  return impl

class Wrapper(TerminalBase):
  def __init__( self, wrapped, wrapper ):
    self.wrapped = wrapped
    self.wrapper = wrapper
    
  def __call__( self, line ):
    result, rest = self.wrapped( line )
    return self.wrapper( result ), rest

def group( number ):
  def impl( token ):
    return token.groups[number]
  return impl
  
class Task(TerminalBase):
  __slots__ = "_typeEnum", "groups", "type", "line", "match", "_re"
  def __init__( self, typeEnum ):
    self.setPattern( typeEnum )

  def setPattern( self, typeEnum ):
      #clear state variables
    self._typeEnum = typeEnum
    self.groups = None
    self.type = None
      #set the regex lookup dict
    self._re = { taskType : re.compile(taskType.value) for taskType in self._typeEnum }
  
    # no deep copying regexes. Members must be immutable
  def __deepcopy__( self, memo ):
    return copy.copy(self)
  
  def __call__( self, line ):
    self.line = line   
    self.type = None
    
    # list comprehension code,. Slower for some reason
    '''taskType, match = next( ( 
      (taskType, match) for (taskType, match) in ( 
        (t, r.match(line)) for (t, r) in self._re.items() 
      ) if match is not None 
    ), (None, None) )
    
    if match is not None:
      self.match = match
      self.type = taskType;
      return self, self.match.string[self.match.end(0):]
    return None, None'''
    
    for taskType, re in self._re.items():
      match = re.match(line)
      if match is not None:
        self.match = match.group()
        self.groups = match.groups()
        self.type = taskType
        return self, match.string[match.end(0):]
    
    raise gen.ParserFailedException()
    
  def __repr__( self ):
    return ( "<Task"
      + ((" type: "+str(self.type)) if self.type else "")
      + ((" groups: "+str(self.groups)) if self.groups else "")
      + ">" )

    
class TaskHandler(Task):
  def __init__( self, handler ):
    self.handler = handler
    super().__init__( handler.enum )
    
  def __call__( self, line ):
    result, rest = Task.__call__( self, line )
    return self.handler( result ), rest
      
class EitherTask(Task):
  def __init__(self, enumTypes ):
    super().__init__( enumTypes )
    
  def setPattern( self, typeEnums ):
      #clear state variables
    self._typeEnum = [list(e) for e in typeEnums]
    self._typeEnum = [item for sublist in self._typeEnum for item in sublist]
    self.groups = None
    self.type = None
      #set the regex lookup list
    self._re = { taskType : re.compile(taskType.value) for taskType in self._typeEnum }

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
