import sympy as sy
import languages.heidenhain.commands as cmd

symbols = sy.symbols('x y z ix iy iz r a ir ia')
x,y,z, ix,iy,iz, r,a, ir,ia = symbols
sym2coord = {
   x : cmd.Cartesian.X,
   y : cmd.Cartesian.Y,
   z : cmd.Cartesian.Z,
   
   ix : cmd.Cartesian.XINC,
   iy : cmd.Cartesian.YINC,
   iz : cmd.Cartesian.ZINC,
   
   r : cmd.Polar.RAD,
   a : cmd.Polar.ANG,
   
   ir : cmd.Polar.RADINC,
   ia : cmd.Polar.ANGINC
}

coord2sym = { value:key for key,value in sym2coord.items() }    

planeCoordDict = {  
    cmd.Plane.XY : (x,y),
    cmd.Plane.YZ : (y,z),
    cmd.Plane.ZX : (z,x)
  }
  
planeCenterDict = {  
    cmd.Plane.XY : (cmd.Center.X,cmd.Center.Y),
    cmd.Plane.YZ : (cmd.Center.Y,cmd.Center.Z),
    cmd.Plane.ZX : (cmd.Center.Z,cmd.Center.X)
  }

planeLenDict = {
    cmd.Plane.XY : cmd.Cartesian.Z,
    cmd.Plane.YZ : cmd.Cartesian.X,
    cmd.Plane.ZX : cmd.Cartesian.Y
  }
  
def invariant( update, state ):
    # Obtain the plane in which the polar motion occurs
  plane = None
  try:
    plane = update[cmd.Registers.POLARPLANE]
  except KeyError:
    plane = state[cmd.Registers.POLARPLANE]
    
  x1, x2   = planeCoordDict[plane]  # get symbols for polar coordinate substitution
  cx1, cx2 = planeCenterDict[plane] # get circle center symbols
  cx1, cx2 = state[cx1], state[cx2] # retrieve circle center values from state
  
  # Substitute polar plane offset LEN
  # as cartesian coordinate value depending on selected plane
  lenCoord = planeLenDict[plane]
  try:
    lenValue = update[cmd.Polar.LEN] # absolute LEN case
  except KeyError:
    lenCoord = cmd.abs2inc[ lenCoord ] 
    try:
      lenValue = update[cmd.Polar.LENINC] # incremental LEN case
    except KeyError:
      lenValue = None
  
  # value is known if belongs to the invariant (is specified in coord2sym) and update contains its value
  knowns   = { coord2sym[coord] : value for coord, value in update.items() if coord in coord2sym }
  # LEN or LENINC occurs in update, substitute the value in knowns
  if lenValue is not None:
    knowns[ coord2sym[lenCoord] ] = lenValue
  # value is unknown if it belongs to the invariant and is not a known
  unknowns = [ unknown for unknown in sym2coord if unknown not in knowns ]
  # previous state is used as init value for numerical solving
  init     = [ state[sym2coord[symbol]] for symbol in unknowns ]
  
  # symbol -> value mapping for injection of known values
  symDict = { key:key for key in symbols }
  symDict.update( knowns )
  
  # build the state invariant equations
  invariant = [
    sy.Eq( symDict[x] - state[cmd.Cartesian.X] - symDict[ix], 0 ), # X = X0 - IX
    sy.Eq( symDict[y] - state[cmd.Cartesian.Y] - symDict[iy], 0 ), # Y = Y0 - IY
    sy.Eq( symDict[z] - state[cmd.Cartesian.Z] - symDict[iz], 0 ), # Z = Z0 - IZ
    
    sy.Eq( symDict[r] - state[cmd.Polar.RAD] - symDict[ir], 0 ),   # R = R0 - IR
    sy.Eq( symDict[a] - state[cmd.Polar.ANG] - symDict[ia], 0 ),   # A = A0 - IA
    
      # Polar and cartesian associations depending on the selected plane
    sy.Eq( cx1 + symDict[r]*sy.cos(symDict[a]) - x1 ),
    sy.Eq( cx2 + symDict[r]*sy.sin(symDict[a]) - x2 )
  ]
  
    # Solve the equations numerially, put the result in a list
    # Solution order matches the order of the unknowns
  solutions = sy.nsolve( invariant, unknowns, init ).T.tolist()[0]
  result = dict(state)  # Copy the state
  result.update(update) # Apply the state update
    # Associate unknowns with solutions and update the result
  result.update( { sym2coord[unknown] : solution for unknown, solution in zip( unknowns, result ) } )
  return result