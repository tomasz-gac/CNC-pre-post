import re
import copy
from generator import Task

  # breaks a line into tokens using a scanner
class Lexer:
  def __init__( self, ws = " " ):
    self._input = ''  # lexer input
    # self.tokens = []  # token list
    self.ws = ws
    self.success = True

  def set( self, line ):
    self._input = line.lstrip( self.ws )
    # self.tokens = []
  
  def hasInput(self):
    return bool(self._input)
  
  def get( self, task ):
    self.success = True
    if not self._input:
      return None # parsed token, parsing success
    
    rest = task.set( self._input )
    if task.groups is not None:
      # self.tokens.append(copy.copy(task))
      self._input = rest.lstrip( self.ws )
      return copy.copy(task) # self.current()
    
    self.success = False
    return None
    
  # def current(self):
  #   return self.tokens[-1] if self.tokens else None
  
  def join( self, fork ):
    self._input = fork._input
    self.ws = fork.ws
    self.success = fork.success
    fork.ws     = " "
    fork._input = ""
    fork.success = True
    
  def fork( self ):
    frk = Lexer()
    frk._input = self._input[:]
    frk.success = self.success
    frk.ws = self.ws
    return frk
    