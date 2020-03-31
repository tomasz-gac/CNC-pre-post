import languages.heidenhain.parser as p
import languages.heidenhain.state as state
import hydra as h
import babel as b
import sys

print('Test 1: ABC')

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
if a.b1.c is not a.b2.c:
  print('test failed')
  input()
 
def decompose_solve( obj, data ):
  decomposition = { type(attr) : attr.value for attr in h.breadth_first(obj) if attr.terminal }
  for attr in decomposition:
    if attr.name == 'inc':
      decomposition[attr] = 0
  obj = h.construct( type(obj), decomposition )
  return h.update( obj, data, decomposition )
  
s = b.State('L Z+150 IX-20 FMAX')
r = p.Parse(s)

print('Test 2: building default')
s0 = state.default()

print('Test 3: linear 1')
s1 = decompose_solve(s0, s.symtable)
tests = [
  s1.target.cartesian.reference.X.abs == -20,
  s1.target.cartesian.reference.X.inc == -20,
  s1.target.cartesian.reference.Z.abs == 150
]
if any( not test for test in tests):
  print('test failed')
  input()
print('Test 4: linear update')

s = b.State('L IX-30 FMAX')
r = p.Parse(s)

s2 = decompose_solve(s1, s.symtable )
tests = [
  s2.target.cartesian.reference.X.abs == -50,
  s2.target.cartesian.reference.X.inc == -30,
  s2.target.cartesian.reference.Z.abs == 150
]
if any( not test for test in tests):
  print('test failed')
  input()

print('Test 5: circle center change')
s = b.State('CC Z-20 Y+30')
r = p.Parse(s)
s3 = decompose_solve(s2, s.symtable)
s = b.State('CC IX-20 IY+30')
r = p.Parse(s)
s3 = decompose_solve(s2, s.symtable)
import time
def do_loop( n ):
  print('Test 6: looping')
  start = time.time()
  s4 = s3
  att4 = None

  for i in range(n):
    s = b.State('LP IPA+20 PR30 FMAX')
    r = p.Parse(s)
    s4 = decompose_solve(s4, s.symtable)
    if s2 is None:
      print('failed ',i)
      break
  print( time.time() - start )

do_loop(200000)
