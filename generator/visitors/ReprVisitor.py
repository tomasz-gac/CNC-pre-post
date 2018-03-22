import generator.visitor as vis

class ReprVisitor(vis.Visitor):
  def __init__(self):
    self._depth = 0
    self._visited = []
    
  def visit( self, rule ):
    self._depth += 1
    result = self._ident()
    if( rule in self._visited ):
      result += "<<Parser " +str(self._visited.index(rule)+1)+ " recursion>>"
    else:
      self._visited.append( rule )
      result += str(len(self._visited)) + ":" + vis.Visitor.visit( self, rule )
    self._depth -= 1
    return result
  
  def _ident( self ):
    s = "|".join(["" for _ in range(self._depth)])
    return s
    
  def Parser( self, rule ):
    return "<Parser\n" + self.visit(rule.rule)+"\n" + self._ident() + ">"
  
  def Handle( self, rule ):
    return "<Handle {rule=\n"+self.visit(rule.rule)+"\n"+self._ident()+">"

  def Transform( self, rule ):
    return "<Transform {handle="+str(rule.handle)+" rule=\n"+self.visit(rule.rule)+"\n"+self._ident()+">"

    
  def Not(self, rule):
    return "<Not {rule=\n" + self.visit(rule.rule) + self._ident() + ">"
    
  def Optional(self, rule):
    return "<Optional { rule=\n" + self.visit(rule.rule) + "\n" + self._ident() + ">"
    
  def Alternative( self, rule ):
    s = "<Alternative { options=\n"
    s += "\n".join( ( self.visit(option) for option in rule.options) )
    return s + "\n" + self._ident() + ">"

  def Sequence( self, rule ):
    s = "<Sequence { sequence=\n"
    s += "\n".join( ( self.visit(item) for item in rule.sequence) )
    return s + "\n" + self._ident() + ">"
    
  def Repeat( self, rule ):
    return "<Repeat {rule =\n" + self.visit(rule.rule) + "\n" + self._ident() + ">"
    
  def Terminal( self, rule ):
    return "<Terminal parser ("+str(rule.handle)+")>"

  def TerminalString( self, rule ):
    return self.Terminal( rule )
    
  def Always( self, rule ):
    return "<Always>"
    
  def Never( self, rule ):
    return "<Never>"
    
  def Ignore( self, rule ):
    return "<Ignore { rule =\n" + self.visit(rule.rule) + "\n" + self._ident() + ">"

  def Push( self, rule ):
    return "<Push, rule =\n" + self.visit(rule.rule) + "\n" + self._ident() + ">"
    
  def Copy( self, rule ):
    return "<Copy, name =" + rule.name + ", rule =\n" + self.visit(rule.rule) + "\n" + self._ident() + ">"

  def Cut( self, rule ):
    return "<Move, name =" + rule.name + ", rule =\n" + self.visit(rule.rule) + "\n" + self._ident() + ">"
    
  def Paste( self, rule ):
    return "<Paste, name =" + rule.name + ", rule =\n" + self.visit(rule.rule) + "\n" + self._ident() + ">"
