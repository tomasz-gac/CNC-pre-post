import languages.heidenhain.commands as cmd
import math

class Invariant:
  def __init__( self, target, associations ):
    self.target = target
    self.associations = associations
    
  def __call__( self, update, state ):
    result = {}
      # self.associations is a key : [f1, f2, ... ] mapping
      # f is a key -> kind function
    for key, fs in self.associations.items():
      for f in fs:
        try:
          kind, value = f( update[key], state )
        except KeyError:
          continue
        if key != kind and kind in update:
          raise RuntimeError('Conflicting values for '+str(kind)+' original:'+str(result[kind])+' calculated:'+str(value))
        result.update( (key, update[key]), (kind, value) )
      
    # if len(result) < len(self.target):
    #   raise RuntimeError('Not enough elements in update provided to maintain the invariant for '+str(self.kind))
    return self.target, result

class Abs2Inc:
  def __init__( self, source ):
    if source not in cmd.absolute:
      raise RuntimeError('Expected absolute source, got '+str(source))
    self.source = source
    
  def __call__( self, value, state ):
    return cmd.abs2inc[ self.source ], value - state[ self.source ]
    
class Inc2Abs:
  def __init__( self, source ):
    if source not in cmd.incremental:
      raise RuntimeError('Expected incremental source, got '+str(source))
    self.source = source
    
  def __call__( self, value, state ):
    return cmd.inc2abs[ self.source ], value + state[ self.source ]
        
def AbsIncInvariant( coordEnum, absolute, incremental ):
  items      = set( coordEnum )
  assoc      = { key : Abs2Inc( key ) for key in items.intersection( absolute ) }
  assoc.update({ key : Inc2Abs( key ) for key in items.intersection( incremental ) })
  return Invariant( coordEnum, assoc.items() )
  
        
        
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
    
    
    