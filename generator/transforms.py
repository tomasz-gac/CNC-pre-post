import generator as gen

def Sink( result, state ):  
  if result is not None:
    state += result
  return None

def Source( fallthrough, state ):
  if isinstance( fallthrough, list ) and len(fallthrough) == 0:
    return state
  if fallthrough is not None:
    raise RuntimeError("Parser returned with fallthrough:" + str(fallthrough) )
  return state

    