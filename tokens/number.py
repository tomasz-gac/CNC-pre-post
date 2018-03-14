from enum import Enum

class NumberTokens(Enum):
  number = '^[+-]?((\\d*[.]\\d+)|(\\d+[.]\\d*)|(\\d+))'
