from enum import Enum, unique

@unique
class expressionTokens(Enum):
  plus   = '[+]'
  minus  = '[-]'
  mult   = '[*]'
  div    = '[/]'
  pow    = '\\^'
  lb     = '\\('
  rb     = '\\)'
  assign = '[=]'
  Q      = 'Q(\\d+)'
  # APTidentifier = '\\d*[a-zA-Z]+[a-zA-Z0-9]*'
