import languages.heidenhain.commands as cmd
import math

class Invariant:
  def __init__( self, kind, invariants, eps = 0.0001 ):
    self.kind = kind
    self.invariants = invariants
    self.eps = eps

  def __call__( self, update, *args ):
    processed = {}
    queue  = dict(update)
    while True:
      try:
        # Get source kind and value from queue
        source, value = queue.popitem()
      except KeyError:
        break # No more elements to process        
      try:
        # process the source : value using the invariants dict
        f = self.invariants[source]
      except KeyError:
        # No invariant associated with source, ignore it
        continue
      target, result = f( value, *args )
      # Check if result is contained in queue and processed and
      # see if the value is consistent within the given tolerance
      queueConsistent     = abs(queue.get(target,result)     - result) < self.eps
      processedConsistent = abs(processed.get(target,result) - result) < self.eps
      # Check if the target is new
      newTarget = target not in queue and target not in processed
      
      if not queueConsistent or not processedConsistent:
        # If the target is already present, raise an error if its value is inconsistent
        # It may have been added by transform function, this ensures that its inverse works properly
        raise RuntimeError('Inconsistent value for '+str(source)+'->'+str(target)+': '+str(value)+' != '+str(result))
      if newTarget:
        # If target is new, add it to the queue for invariant processing
        queue[target] = result
      
      # source has been processed consistently
      # it's okay to overwrite in case when source == target
      processed[source] = value
      processed[target] = result
    return self.kind, processed

    
    
class Abs2Inc:
  def __init__( self, source ):
    if cmd.isIncremental(source):
      raise RuntimeError('Expected absolute source, got '+str(source))
    self.source = source
    
  def __call__( self, value, state ):
    return cmd.abs2inc(self.source), value - state[self.source]

class Inc2Abs:
  def __init__( self, source ):
    if cmd.isAbsolute(source):
      raise RuntimeError('Expected incremental source, got '+str(source))
    self.source = source
    
  def __call__( self, value, state ):
    return cmd.inc2abs(self.source), value + state[self.source]
        
def toIncInvariant( absolute ):
  invariants = { key : Abs2Inc(key) for key in list(absolute) }
  return invariants
  
def toAbsInvariant( incremental ):
  invariants = { key : Inc2Abs(key) for key in list(incremental) }
  return invariants
        
# cartesian mappings for polar calculation
planeCoordDict = {  
    cmd.Plane.XY : (cmd.Cartesian.X,cmd.Cartesian.Y,cmd.Cartesian.Z),
    cmd.Plane.YZ : (cmd.Cartesian.Y,cmd.Cartesian.Z,cmd.Cartesian.X),
    cmd.Plane.ZX : (cmd.Cartesian.Z,cmd.Cartesian.X,cmd.Cartesian.Y)
  }
# circle center mappings for polar calculation
planeCenterDict = {  
    cmd.Plane.XY : (cmd.Center.X,cmd.Center.Y),
    cmd.Plane.YZ : (cmd.Center.Y,cmd.Center.Z),
    cmd.Plane.ZX : (cmd.Center.Z,cmd.Center.X)
  }

def angNorm( a ):
  return (a+2*math.pi) % (2 * math.pi)
  
def Cartesian2Polar(update, state ):
    union = dict(state)
    union.update(update)
    
    plane = union[cmd.Registers.POLARPLANE]
    x1, x2, x3 = planeCoordDict[plane] # get cartesian coordinates for substitution
    cx1, cx2 = planeCenterDict[plane]  # get circle center coordinates
    
    r1, r2 = (update[x1]-union[cx1]), (update[x2]-union[cx2])
    
    update[ cmd.Polar.RAD ] = math.sqrt(r1**2 + r2**2)
    update[ cmd.Polar.ANG ] = angNorm(math.atan2(r2, r1)) * float(180)/math.pi
    update[ cmd.Polar.LEN ] = update[ x3 ]
    
    incFromAbs( cmd.Polar.RAD, update, state )
    incFromAbs( cmd.Polar.ANG, update, state )
    incFromAbs( cmd.Polar.LEN, update, state )
    

def Polar2Cartesian( update, state ):
    union = dict(state)
    union.update(update)
    
    plane = union[cmd.Registers.POLARPLANE]
    x1, x2   = planeCoordDict[plane]   # get cartesian coordinates for substitution
    x3       = planeNormDict[plane]    # get cartesian LEN offset coordinate
    cx1, cx2 = planeCenterDict[plane]  # get circle center coordinates
    
    update[ x1 ] = union[ cx1 ] + update[ cmd.Polar.RAD ]*math.cos(update[ cmd.Polar.ANG ]*math.pi/180)
    update[ x2 ] = union[ cx2 ] + update[ cmd.Polar.RAD ]*math.sin(update[ cmd.Polar.ANG ]*math.pi/180)
    update[ x3 ] = update[ cmd.Polar.LEN ]
    
    incFromAbs( x1, update, state )
    incFromAbs( x2, update, state )
    incFromAbs( x3, update, state )
    
    
    