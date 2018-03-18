class ParserFailedType:
  def __call__( self, result, success ):
    return type(result) == ParserFailedType

ParserFailed = ParserFailedType()