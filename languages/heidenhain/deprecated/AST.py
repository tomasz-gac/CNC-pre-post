from enum import Enum, unique
import collections as coll

@unique
class CoordinateSymbols(Enum):
  X = 'X'
  Y = 'Y'
  Z = 'Z'
  A = 'A'
  B = 'B'
  C = 'C'
  R = 'R'

@unique
class Compensation(Enum):
  none = 0
  left = 1
  right = 2

@unique
class CircleDirection(Enum):
  cw = 0
  ccw = 1

@unique
class MovementModes(Enum):
  linear    = 0
  circular  = 1

class SetState:
  def __init__(self):
    pass
  
  def merge( self, states ):
    for state in states:
      for key, value in state.__dict__.items():
        setattr(self, key, value)
        
  def __repr__( self ):
    return "SetState: {" + ", ".join(["{0} : {1}".format(key, value) for key, value in self.__dict__.items()]) + "}"

class PushState:
  def __init__(self, var):
    self.var = var

  def __repr__( self ):
    return "Push state : " + self.var

class PopState:
  def __init__(self, var):
    self.var = var
  
  def __repr__( self ):
    return "PopState: " + self.var

    
class LineNumber:
  def __init__( self, n ):
    self.number = n
  def __repr__(self):
    return '{0}:'.format(self.number)
class Remark:
  def __init__(self, text ):
    self.text = text
  def __repr__(self ):
    return 'Remark: {0}'.format(self.text)
class GOTO:
  def __init__(self, target, polar):
    self.target = target
    self.polar = polar
  def __repr__(self):
    return "GOTO statement to {0}. Polar:{1}".format( self.target.__repr__(), self.polar)
class SetCircleCenter:
  def __init__(self, target):
    self.target = target
  def __repr__(self):
    return "Circle center at {0}".format(self.target.__repr__())
class AuxilaryFunction:
  def __init__(self, number):
    self.number = number
  def __repr__(self):
    return "Auxilary function {0}".format(self.number)
class Coordinate:
  def __init__( self, value, incremental, polar ):
    self.value = value
    self.incremental = incremental
    self.polar = polar
  def __repr__( self ):
    repr = ''
    if self.incremental: repr += 'I'
    if self.polar: repr += 'P'
    return repr + str(self.value)
  def __str__( self ):
    return self.__repr__()
  def updateCartesian( self, value, symtable ):
    if self.polar:
      raise RuntimeError('Treating polar coordinate as cartesian during an update')
    return self.value.evaluate( symtable ) + ( value if self.incremental else 0 )
    
@unique
class ExprOperators(Enum):
  plus    = '+'
  minus   = '-'
  mult    = '*'
  div     = '/'
  pow     = '^'
  assign  = '='

class ExprTerminal:
  def __init__(self, value):
    if value is None:
      raise ValueError('Expected a floating-point value')
    self.value = value
  def evaluate( self, symtable ):
    return self.value
  def __repr__( self):
    return '<Value:'+str(self.value)+'>'
  def __str__( self ):
    return str(self.value)

class ExprVariable:
  def __init__(self, number):
    if number is None or number < 0:
      raise ValueError('Expected a positive integer as variable identifier')
    self.number = number
  def evaluate( self, symtable ):
    value = symtable.get(self.number)
    if value is None:
      raise RuntimeError('Unknown variable Q'+str(self.number))
    else:
      return value
  def __repr__( self):
    return '<Q'+str(self.number)+'>'
  def __str__( self):
    return 'Q'+str(self.number)

class ExprUnary:
  def __init__(self, rhs, operator):
    if rhs is None:
      raise ValueError('Expected a floating-point rhs value')
    if operator is None:
      raise ValueError('Invalid unary operator')
    self.rhs = rhs
    self.operator = operator
  def evaluate( self, symtable ):
    if self.operator is ExprOperators.minus:
      return -self.rhs.evaluate(symtable)
    else:
      raise RuntimeError('Unknown unary operator:"'+str(self.operator)+'"')
  def __repr__( self):
    return self.operator.value + self.rhs.__repr__()
  def __str__( self):
    return self.operator.value + str(self.rhs)

class ExprBinary:
  def __init__(self, lhs, rhs, operator):
    if rhs is None:
      raise ValueError('Expected a floating-point rhs value')
    if lhs is None:
      raise ValueError('Expected a floating-point lhs value')
    if operator is None:
      raise ValueError('Invalid binary operator')
    self.lhs = lhs
    self.rhs = rhs
    self.operator = operator
  def evaluate( self, symtable ):
    if self.operator is ExprOperators.assign:
      result = self.rhs.evaluate(symtable)
      symtable[self.lhs.number] = result
      return result
    elif self.operator is ExprOperators.plus:
      return self.lhs.evaluate(symtable) + self.rhs.evaluate(symtable)
    elif self.operator is ExprOperators.minus:
      return self.lhs.evaluate(symtable) - self.rhs.evaluate(symtable)
    elif self.operator is ExprOperators.mult:
      return self.lhs.evaluate(symtable) * self.rhs.evaluate(symtable)
    elif self.operator is ExprOperators.div:
      return self.lhs.evaluate(symtable) / self.rhs.evaluate(symtable)
    elif self.operator is ExprOperators.pow:
      return self.lhs.evaluate(symtable) ** self.rhs.evaluate(symtable)
    else:
      raise RuntimeError('Unknown binary operator :"'+str(self.operator)+'"')
  def __repr__( self):
    return self.lhs.__repr__() + self.operator.value + self.rhs.__repr__()
  def __str__( self):
    return str(self.lhs) + self.operator.value + str(self.rhs)