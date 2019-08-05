import sympy as sy
import languages.heidenhain.commands as cmd

# machine state coordinates that are used in state invariant
stateCoordinates = set(cmd.Cartesian).union(set(cmd.Polar))
# machine state symbols that correspond to coordinates
stateSymbols = sy.symbols('x:'+str(len(stateCoordinates)))
# symbol -> coordinate and coordinate -> symbol mappings
coord2sym = dict( zip( stateCoordinates, stateSymbols ) )
sym2coord = { value:key for key,value in coord2sym.items() }

# cartesian mappings for polar calculation
planeCoordDict = {  
    cmd.Plane.XY : (cmd.Cartesian.X,cmd.Cartesian.Y),
    cmd.Plane.YZ : (cmd.Cartesian.Y,cmd.Cartesian.Z),
    cmd.Plane.ZX : (cmd.Cartesian.Z,cmd.Cartesian.X)
  }
planeNormDict = { 
    cmd.Plane.XY : cmd.Cartesian.Z,
    cmd.Plane.YZ : cmd.Cartesian.X,
    cmd.Plane.ZX : cmd.Cartesian.Y
  }
# circle center mappings for polar calculation
planeCenterDict = {  
    cmd.Plane.XY : (cmd.Center.X,cmd.Center.Y),
    cmd.Plane.YZ : (cmd.Center.Y,cmd.Center.Z),
    cmd.Plane.ZX : (cmd.Center.Z,cmd.Center.X)
  }
  
  # Function calculates the new machine state depending on
  # the previous state and state update by maintaining an invariant
  # between a set of state variables specified in stateCoordinates
def invariant( update, state ):
  result = dict(state)  # Copy the state
    # Apply the state update, invariant is not maintained at this point
  result.update(update) 
  
    # Obtain the plane that defines the polar motion
  plane = result[cmd.Registers.POLARPLANE]
  x1, x2   = planeCoordDict[plane]   # get cartesian coordinates for substitution
  x3       = planeNormDict[plane]    # get cartesian LEN offset coordinate
  cx1, cx2 = planeCenterDict[plane]  # get circle center coordinates
  
  # value is known if belongs to the invariant (is specified in stateCoordinates) and update contains its value
  knowns   = { coord : update[coord] for coord in stateCoordinates.intersection(update.keys()) }
  # coordinate -> value mapping for known value injection
  # if value is unknown, it defaults to sympy symbol for computation
  symbols = dict( coord2sym )
  symbols.update( knowns )
  
  # build the state invariant equations
  invariant = [
    sy.Eq( symbols[cmd.Cartesian.X] - state[cmd.Cartesian.X] - symbols[cmd.Cartesian.XINC], 0 ),
    sy.Eq( symbols[cmd.Cartesian.Y] - state[cmd.Cartesian.Y] - symbols[cmd.Cartesian.YINC], 0 ),
    sy.Eq( symbols[cmd.Cartesian.Z] - state[cmd.Cartesian.Z] - symbols[cmd.Cartesian.ZINC], 0 ),
    
    sy.Eq( symbols[cmd.Polar.RAD] - state[cmd.Polar.RAD] - symbols[cmd.Polar.RADINC], 0 ),
    sy.Eq( symbols[cmd.Polar.ANG] - state[cmd.Polar.ANG] - symbols[cmd.Polar.ANGINC], 0 ),
    sy.Eq( symbols[cmd.Polar.LEN] - state[cmd.Polar.LEN] - symbols[cmd.Polar.LENINC], 0 ),
    
      # Polar and cartesian associations depending on the selected plane
      # Polar center coordinates taken from result to accomodate for update
    sy.Eq( result[cx1] + symbols[cmd.Polar.RAD]*sy.cos(symbols[cmd.Polar.ANG]) - symbols[x1], 0 ),
    sy.Eq( result[cx2] + symbols[cmd.Polar.RAD]*sy.sin(symbols[cmd.Polar.ANG]) - symbols[x2], 0 ),
    sy.Eq( symbols[cmd.Polar.LEN] - symbols[x3], 0 )
  ]
  # print(invariant)
  
  # f = lambdify(fargs, f.T, modules)
  # J = lambdify(fargs, J, modules)
    # solve the system numerically
  # x = findroot(f, x0, J=J, **kwargs)
  
  # value is unknown if it belongs to the invariant and is not a known
  unknownCoords  = stateCoordinates.difference( knowns )
  unknownSymbols = [ coord2sym[unknown] for unknown in unknownCoords ]
  # previous state is used as init value for numerical solving
  init           = [ state[unknown]     for unknown in unknownCoords ]
  
  requiredKnownCount = len(stateCoordinates) - len(inv)
  if len(knowns) < requiredKnownCount:
    raise RuntimeError('Invalid state update, expected '+str(requiredKnownCount)+' known values, got '+str(len(knowns))+'.')
  
    # Solve the equations numerially, put the result in a list
    # Solution order matches the order of the unknowns
  solutions = sy.nsolve( inv, unknownSymbols, init ).T.tolist()[0]
    # Associate unknowns with solutions and update the result
  result.update( zip( unknownCoords, solutions ) )
  return result
  
from babel import State  
from languages.heidenhain.parser import Parse
  
def bench( n = 1000 ):
  import time
  start = time.time()
  q = None
  r = None
  s0 = cmd.StateDict()
  for i in range(n):
    q = State( 'L X+50 Y-30 Z+150 R0 FMAX' )
    r = Parse( q )
    s = invariant( q.symtable, s0 )
  print( time.time() - start )
  print(q.symtable)
  print(r)
