import languages.heidenhain.parser as p
import languages.heidenhain.commands as cmd
import hydra as h
import babel as b

s = b.State('L Z+150 IX-20 FMAX')
r = p.Parse(s)

class Cartpol(h.Morph):
  cartesian = cmd.Cart
  polar = cmd.Pol
  
c,i = h.solve(Cartpol, s.symtable, cmd.StateDict())

s = b.State('L IX-30 FMAX')
r = p.Parse(s)

dec = cmd.StateDict()
dec.update( { type(attr) : attr.value for attr in h.breadth_first(c) if attr.terminal } )
c = h.update(c, s.symtable, dec)

def bench( n = 1000 ):
  import time
  start = time.time()
  s = None
  r = None
  prevState = cmd.StateDict()
  solution, conflicts = h.solve(Cartpol, prevState, cmd.StateDict())
  prevState = { key : value for key,value in prevState.items() if not isinstance( key, h.MemberMeta ) or key.terminal }
  for i in range(n):
    s = b.State( 'L IX+50 Y-30 Z+150 R0 FMAX' )
    r = p.Parse( s )
    solution = h.update(solution, s.symtable, prevState )
    prevState.update( { type(attr) : attr.value for attr in h.breadth_first(solution) if attr.terminal } )
  print( time.time() - start )
  print(s.symtable)
  print(r)
  return solution, prevState

  
def test( sol=None, prevState=None ):
  if prevState is None:
    prevState = cmd.StateDict()
  # Konstruowanie solution ze StateDict jest ok, a z prevState nie
  solution = sol
  if sol is None:
    solution, conflicts = h.solve(Cartpol, prevState, cmd.StateDict())    
    prevState = { key : value for key,value in prevState.items() if not isinstance( key, h.MemberMeta ) or key.terminal }
  
  s = b.State( 'L IX+50 Y-30 Z+150 R0 FMAX' )
  r = p.Parse( s )
  solution = h.update(solution, s.symtable, prevState )
  prevState.update( { type(attr) : attr.value for attr in h.breadth_first(solution) if attr.terminal } )
  return solution, prevState