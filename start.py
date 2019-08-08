import languages.heidenhain.parser as p
import languages.heidenhain.state as state
import hydra as h
import babel as b

def main():
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
    s1.cartesian.cartesian.X.abs == -20,
    s1.cartesian.cartesian.X.inc == -20,
    s1.cartesian.cartesian.Z.abs == 150
  ]
  if any( not test for test in tests):
    print('test failed')
    input()
  print('s2 : linear update')

  s = b.State('L IX-30 FMAX')
  r = p.Parse(s)

  s2, att2 = decompose_solve(s1, s.symtable )
  tests = [
    s2.cartesian.cartesian.X.abs == -50,
    s2.cartesian.cartesian.X.inc == -30,
    s2.cartesian.cartesian.Z.abs == 150
  ]
  if any( not test for test in tests):
    print('test failed')
    input()

  print('s3 : circle center change')
  # s = b.State('L IX-30 IZ+5 FMAX')
  s = b.State('CC X-20 Y+30')
  r = p.Parse(s)
  s.symtable.update({
    state.Cartesian.X.attr.inc : 0,
    state.Cartesian.Y.attr.inc : 0,
    state.Cartesian.Z.attr.inc : 0
  })
  s3, att3 = decompose_solve(s2, s.symtable)
  print('s4 : looping')


  import time
  start = time.time()
  s4 = s3
  att4 = None

  for i in range(15000):
    s = b.State('L X+20 IY-3 Z+150 FMAX')
    r = p.Parse(s)
    s.symtable.update({
      state.Center.CX.attr.inc : 0,
      state.Center.CY.attr.inc : 0,
      state.Center.CY.attr.inc : 0
    })
    s4, att4 = decompose_solve(s4, s.symtable)
    if s2 is None:
      print('failed ',i)
      break
  print( time.time() - start )
  
if __name__ == "__main__":
  main()