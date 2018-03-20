import generator as gen


def Pipe():
  class Sink:
    def __init__( self ):
      self.name = 'result_'+str(id(self))
    def __call__( self, result, state ):  
      if gen.ParserFailed( result, True ):
        return ParserFailed, state
      elif result is not None:
        try:
          r = getattr( state, self.name )
          r += result
        except AttributeError:
          setattr( state, self.name, result )
      return None
    
    def extract( self, state ):
      result = getattr( state, self.name )
      setattr( state, self.name, [] )
      return result

  class Source:
    def __init__( self, sink ):
      self._sink = sink
    
    @property
    def sink( self ):
      return self._sink

    def __call__( self, fallthrough, state ):
      if gen.ParserFailed( fallthrough, True ):
        return gen.ParserFailed, state
      if fallthrough is not None:
        raise RuntimeError("Parser returned with fallthrough:" + str(fallthrough) )
      return self.sink.extract(state)

  s = Sink()
  return s, Source(s)
