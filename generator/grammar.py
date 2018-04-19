import generator.rule as r

class Grammar(object):
  def __setattr__( self, name, value ):
    if isinstance( value, r.Rule ):
      value.name = name
    d = object.__getattribute__(self,'__dict__')
    d[name] = r.make(value)
    
  def __getattribute__( self, name ):
    d = object.__getattribute__(self,'__dict__')
    try:      
      return d[name]
    except KeyError:
      rule = r.Terminal()
      rule.name = name
      return rule
      
