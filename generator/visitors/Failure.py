class ParserFailedType:
  def __call__( self, result, success ):
    return type(result) == ParserFailedType

ParserFailed = ParserFailedType()

class ParserResult:
  def __init__( self ):
    self.result = []