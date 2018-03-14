import generator.visitor as vis

class StrVisitor:
  def __init__(self):
    self._visited = []
    
  def visit( self, rule ):
    result = ""
    if( rule in self._visited ):
      result += "<<Recursion>>"
    else:
      self._visited.append( rule )
      result += vis.Visitor.visit( rule )
    return result
  
  def Handle( self, rule ):
    return rule.rule.accept(self)

  def Not(self, rule):
    return "-(" + rule.rule.accept(self) + ")"
    
  def Optional(self, rule):
    return "~(" + rule.rule.accept( self ) + ")"
    
  def Alternative( self, rule ):
    return "( " + " | ".join( ( option.accept( self ) for option in rule.options) ) + " )"

  def Sequence( self, rule ):
    return "( " + " & ".join( ( item.accept( self ) for item in rule.sequence) ) + " )"
    
  def Repeat( self, rule ):
    return "+( " + rule.rule.accept(self) + " )"
    
  def Terminal( self, rule ):
    return "<Terminal parser ("+str(rule.task._typeEnum)+")>"

  def TerminalString( self, rule ):
    return self.Terminal( rule )
