from enum import Enum
import math

class Invariant(Enum):
  '''def __init__( self, enum=None, transform = lambda tag, x, *args: x ): #, test = lambda x, y : True ):
    self.enum       = enum
    if self.enum is None:
      self.structure  = {}
      self.invariants = {}
    else:
      self.structure  = { kind.value.enum : kind for kind in self.enum if kind.value.enum is not None }
      self.invariants = { kind : kind.value.transform for kind in self.enum }
    self.transform  = transform
    # self.test       = test'''
    
  def __new__(cls, transform):
    value = len(cls.__members__) + 1
    obj = object.__new__(cls)
    obj._value_ = value
    print(cls, transform)
    return obj
    
  def __call__( self, tag, update, *args ):
    processed = {}
    queue  = dict(update)
    
    while True:
      try:
        # Get source and value from queue
        source, value = queue.popitem()
      except KeyError:
        break # No more elements to process        
      if not callable(source):
          # source encodes no transformation, ignore it
        continue
      '''try:
        # process the source : value using the invariants dict
        f = self.invariants[source]
      except KeyError:
        # No invariant associated with source, ignore it
        continue'''
      # append for consistency checks in case source == target
      processed[source] = value
      
      results = source( value, *args )
      for target, result in results.items():
        # Check if result is contained in queue and processed and
        # see if the value is consistent using the test function
        queueConsistent     = queue.get(target,result)     == result # self.test( queue.get(target,result),     result )
        processedConsistent = processed.get(target,result) == result # self.test( processed.get(target,result), result )
        # Check if the target is new
        newTarget = target not in queue and target not in processed
        
        if not queueConsistent or not processedConsistent:
          # If the target is already present, raise an error if its value is inconsistent
          # It may have been added by transform function, this ensures that its inverse works properly
          raise RuntimeError('Inconsistent value for '+str(source)+':'+str(value)+'->'+str(target)+':'+str(result))
        if newTarget:
          # If target is new, add it to the queue for invariant processing
          queue[target] = result
        
      # source has been processed consistently
      # it's okay to overwrite in case when source == target
      processed.update( results )
    
    return processed
    
  '''def gather( self, processed ):
    collected = dict(processed)
    for enum in self.structure:
      collected.update( enum.gather(collected) )
    
    # gather processed elements according to self.structure
    for key, value in processed.items():
      # enum value -> enum class
      if type(key) in self.structure:
        tag = self.structure[type(key)]
        try:
          # append the element to the tag
          collected[tag][key] = value
        except KeyError:
          collected[tag] = { key : value }
    # Remove all incomplete gathered groups
    for enum, tag in self.structure.items():
      if tag in collected and len(enum) != len(collected[tag]):
        collected.pop(tag)
    return collected'''
       
'''class AbsIncInvariant(Invariant):
  def __init__( self, classes ):  
    invariants = {}
    for e in classes:
      if cmd.isAbsolute( e ):
        invariants.update( { key : Abs2Inc(key) for key in list(e) } )
        invariants.update( { key : Inc2Abs(key) for key in list(e.incremental) } )
      else:
        invariants.update( { key : Inc2Abs(key) for key in list(e) } )
        invariants.update( { key : Abs2Inc(key) for key in list(e.absolute) } )
      
    super().__init__( invariants, test=lambda x, y : abs( x - y ) < 0.0001 )
    
  def __call__( self, update, *args ):
    result = super().__call__( update, *args )
    return { AbsIncInvariant : result }
  
def coordCollector( update, *args ):
    collected = {}
    for key, value in update.items():
      enum = key.__objclass__
      if enum in collected.keys():
        collected[enum][key] = value
      else:
        collected[enum] = { key : value }
    return { enum : values for enum,values in collected.items() if len(values) == len(enum) }
    
class RebuildState(Invariant):
  def __init__(self):
    invariants = { 
      None            : AbsIncInvariant([cmd.Cartesian, cmd.Polar, cmd.Angular, cmd.Center]),
      AbsIncInvariant : coordCollector
    }
    super().__init__( invariants )
    
  def __call__( self, update, *args ):
    result = super().__call__( update, *args )
    return { RebuildState : result }'''
        
# cartesian mappings for polar calculation
'''planeCoordDict = {  
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
    incFromAbs( x3, update, state )'''
    
    
    