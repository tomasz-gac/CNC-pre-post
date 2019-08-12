import languages.heidenhain.parser as p
import languages.heidenhain.state as state
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

def decompose_solve( obj, data ):
  decomposition = state.StateDict()
  decomposition.update( { type(attr) : attr.value for attr in h.breadth_first(obj) if attr.terminal } )
  return h.update(obj, data, decomposition)

  
s = b.State('L Z+150 IX-20 FMAX')
r = p.Parse(s)

print('s0')
s0, i, sh = h.solve(state.Position, state.StateDict(), state.StateDict())
s00,i, sh = h.solve(state.Position, state.StateDict(), state.StateDict())
# print(s0 == s00)
print('s1 : linear 1')
# input()
s1, att1 = decompose_solve(s0, s.symtable)
tests = [
  s1.cartesian.reference.X.abs == -20,
  s1.cartesian.reference.X.inc == -20,
  s1.cartesian.reference.Z.abs == 150
]
if any( not test for test in tests):
  print('test failed')
  input()
print('s2 : linear update')

s = b.State('L IX-30 FMAX')
r = p.Parse(s)

s2, att2 = decompose_solve(s1, s.symtable )
tests = [
  s2.cartesian.reference.X.abs == -50,
  s2.cartesian.reference.X.inc == -30,
  s2.cartesian.reference.Z.abs == 150
]
if any( not test for test in tests):
  print('test failed')
  input()

print('s3 : circle center change')
s = b.State('CC Z-20 Y+30')
r = p.Parse(s)
s.symtable.update({
  state.Point.X.attr.inc : 0,
  state.Point.Y.attr.inc : 0,
  state.Point.Z.attr.inc : 0
})
s3, att3 = decompose_solve(s2, s.symtable)
print('s4 : looping')


import time
start = time.time()
s4 = s3
att4 = None

for i in range(200000):
  s = b.State('LP IPA+20 PR30 FMAX')
  r = p.Parse(s)
  s.symtable.update({
    state.Origin.CX.attr.inc : 0,
    state.Origin.CY.attr.inc : 0,
    state.Origin.CZ.attr.inc : 0
  })
  s4, att4 = decompose_solve(s4, s.symtable)
  if s2 is None:
    print('failed ',i)
    break
print( time.time() - start )