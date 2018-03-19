import re
import copy
from generator import Task

  # breaks a line into tokens using a scanner
class Lexer:
  def __init__( self, transform = lambda x : x, pp = lambda s : s.lstrip(' ') ):
    self._input = ''  # lexer input
    self.preprocess = pp
    self.transform = transform
    self.success = True

  def set( self, line ):
    self._input = self.preprocess( line )
  
  def hasInput(self):
    return bool(self._input)
  
  def get( self, task ):
    self.success = True
    if not self._input:
      return None
    
    result, rest = task( self._input )
    if rest is not None:
      self.set(rest)
      return self.transform(result)
    
    self.success = False
    return None
  
  def join( self, fork ):
    self._input = fork._input
    self.success = fork.success
    self.preprocess = fork.preprocess
    self.transform = fork.transform
    
  def fork( self ):
    frk = Lexer()
    frk._input = self._input[:]
    frk.success = self.success
    frk.preprocess = self.preprocess
    frk.transform = self.transform
    return frk
    