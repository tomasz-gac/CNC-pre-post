import re
import itertools
from enum import Enum, unique
import copy

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
  def __init__( self, typeEnum ):
    self.setPattern( typeEnum )

  def setPattern( self, typeEnum ):
      #clear state variables
    self._typeEnum = typeEnum
    self.groups = None
    self.type = None
      #set the regex lookup dict
    self._re = { taskType : re.compile(taskType.value) for taskType in self._typeEnum }
    
  
  def set( self, line ):
    self.line = line   
    self.type = None
    self.groups = None
    self.match = None
    
    # list comprehension code, remember to assign values with code from loop
    # slower for some reason
    '''match, taskType = next(                         #first of:
       ( (re, t) for (re, t) in                     # regex, token pair from:
         zip( (r.match(line) for r in self._re), self._typeEnum) #(match line for each _re, typeEnum )
           if re is not None                                     #add if matched
       )
     , (None, None) # default value
     )'''
    
    for taskType, re in self._re.items():
      match = re.match(line)
      if match is not None:
        self.match = match.group()
        self.groups = match.groups()
        self.type = taskType;
        return self, match.string[match.end(0):]
    
    return None, None
    
  def __repr__( self ):
    return ( "<Task"
      + ((" type: "+str(self.type)) if self.type else "")
      + ((" groups: "+str(self.groups)) if self.groups else "")
      + ">" )

class HandledTask(Task):
  def __init__( self, handler ):
    self.handler = handler
    Task.__init__( self, handler.enum )
    
  def set( self, line ):
    result, rest = Task.set( self, line )
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
    