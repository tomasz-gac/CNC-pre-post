import re
import itertools
from enum import Enum, unique
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
      #set the handle method in Handler
    # default handler
    # Handler._dispatch[None] = Handler.default
    Handler.__call__ = _doHandle
    Handler.handled = self.tasks
    return Handler
    
class Task:
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
    
    # list comprehension code, remember to assign values with code from loop
    # slower for some reason
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

class HandledTask(Task):
  def __init__( self, handler ):
    self.handler = handler
    Task.__init__( self, handler.enum )
    
  def __call__( self, line ):
    result, rest = Task.__call__( self, line )
    if rest is not None:
      return self.handler( result ), rest
    return result, rest
      
class EitherTask(Task):
  def __init__(self, enumTypes ):
    Task.__init__( self, enumTypes )
    
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
    Task.__init__( self, rex )
    
  def setPattern( self, rex ):
      #clear state variables
    self._typeEnum = rex
    self.groups = None
    self.type = None
      #set the regex lookup list
    self._re = { None : re.compile(rex) }
    