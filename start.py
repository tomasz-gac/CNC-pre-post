import languages.heidenhain.parser as p
import languages.heidenhain.commands as cmd
import hydra as h
import babel as b

class C(h.Morph):
  common = int

class B1(h.Morph):
  c = C
  x = int

class B2(h.Morph):
  c = C
  x = float

class A(h.Morph):
  b1 = B1
  b2 = B2
  
init = { attr : attr.value() for attr in h.breadth_first(A) if attr.terminal }
a, i = h.solve( A, init )

class Cartpol(h.Morph):
  cartesian = cmd.Cartesian
  polar = cmd.Polar

s = b.State('L Z+150 IX-20 FMAX')
r = p.Parse(s)

print('s0')
input()  
s0,i = h.solve(Cartpol, cmd.StateDict(), cmd.StateDict())
d0 = cmd.StateDict()
print('s1')
input()
s1, att = h.update(s0, s.symtable, d0)
# print(s1)
d1 = { type(attr) : attr.value for attr in h.breadth_first(s1) if attr.terminal }

s = b.State('L IX-30 FMAX')
r = p.Parse(s)

# dec = cmd.StateDict()
# dec.update( { type(attr) : attr.value for attr in h.breadth_first(c) if attr.terminal } )
s2, att2 = h.update(s1, s.symtable, d1)

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