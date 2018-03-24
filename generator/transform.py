import generator as gen

def Sink( result, parser ):  
  if result is not None:
    parser.state += result
  return None

def Source( fallthrough, parser ):
  result, parser.state = parser.state, []
  if isinstance( fallthrough, list ) and len(fallthrough) == 0:
    return result
  if fallthrough is not None:
    raise RuntimeError("Parser returned with fallthrough:" + str(fallthrough) )
  return result

    