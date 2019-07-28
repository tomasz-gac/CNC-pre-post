import languages.heidenhain.type as t

class Q( t.Morph ):
  X = float
  Y = bool
  Z = int
  
class P( t.Morph ):
  X = str
  Y = dict
  Z = list
  
class R( t.Morph ):
  Q = Q
  P = P
  F = int
  
d = { Q.X : 1.1, Q.Y : True, Q.Z : 2, P.X : '123', P.Y : {}, P.Z : [] }
DD = { R.Q : Q.solve(d), R.P : P.solve(d), R.F : 2 }
