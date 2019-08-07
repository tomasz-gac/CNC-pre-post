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
a, i, sh = h.solve( A, init )

class Cartpol(h.Morph):
  cartesian = cmd.Cartesian
  polar = cmd.Polar

def decompose_solve( obj, data ):
  decomposition = cmd.StateDict()
  decomposition.update( { type(attr) : attr.value for attr in h.breadth_first(obj) if attr.terminal } )
  return h.update(obj, data, decomposition)

  
s = b.State('L Z+150 IX-20 FMAX')
r = p.Parse(s)

print('s0')
s0,i, sh = h.solve(Cartpol, cmd.StateDict(), cmd.StateDict())
print('s1 : linear 1')
s1, att1 = decompose_solve(s0, s.symtable)
tests = [
  s1.cartesian.absolute.X == -20,
  s1.cartesian.incremental.X == -20,
  s1.cartesian.absolute.Z == 150
]
if any( not test for test in tests):
  print('test failed')
  input()
print('s2 : linear update')

s = b.State('L IX-30 FMAX')
r = p.Parse(s)

s2, att2 = decompose_solve(s1, s.symtable )
tests = [
  s2.cartesian.absolute.X == -50,
  s2.cartesian.incremental.X == -30,
  s2.cartesian.absolute.Z == 150
]
if any( not test for test in tests):
  print('test failed')
  input()

print('s3 : circle center change')
s = b.State('L IX-30 IZ+5 FMAX')
# s = b.State('CC X-20 Y+30')
r = p.Parse(s)
'''s.symtable.update({
  Cartpol.cartesian.incremental.attr.X : 0,
  Cartpol.cartesian.incremental.attr.Y : 0,
  Cartpol.cartesian.incremental.attr.Z : 0
})'''

import time
start = time.time()

s2, att3 = decompose_solve(s2, s.symtable)
'''for i in range(100000):
  print(i)
  s2, att3 = decompose_solve(s2, s.symtable)
  #  i % 1000 == 0:
  print(i)
  if s2 is None:
    print('failed ',i)
    break'''
print( time.time() - start )