import enum
from math import isclose

class Member:
  __slots__ = 'instance', 'name'
  def __init__( self, instance, name ):
    self.instance = instance
    self.name     = name
    self.terminal = not hasattr(getattr(instance,name), 'members')
  
  # This has to be a property because Members serve as keys
  # and their value cannot take part in hasing
  @property
  def value( self ):
    return getattr( self.instance, self.name )
    
  @value.setter
  def value( self, value ):
    setattr( self.instance, self.name, value )
    
  def __repr__( self ):
    return '%s.%s' % (self.instance, self.name)    


class MemberMeta(type):
  __slots__ = 'instance', 'name'
  def __new__(metacls, cls, bases, classdict ):
    cls_instance = super().__new__(metacls, cls, bases+(Member,), classdict)
    cls_instance.instance = classdict['instance']
    cls_instance.name = classdict['name']
    cls_instance.terminal = not hasattr(getattr(cls_instance.instance,cls_instance.name), 'members')
    return cls_instance
    
  # This has to be a property because Members serve as keys
  # and their value cannot take part in hasing
  @property
  def value( self ):
    return getattr( self.instance, self.name )
    
  @value.setter
  def value( self, value ):
    setattr( self.instance, self.name, value )
    
  def __repr__( self ):
    return '%s.%s' % (self.instance, self.name)    

class Members:
  def __init__( self, instance ):
    self._members_ = []
    for memberType in type(instance).members:
      member = memberType(instance, memberType.name)
      setattr( self, member.name, member )
      self._members_.append(member)
    
    self._member_names_ = { member.name for member in self._members_ }
  
  def __contains__(self, member):
    return isinstance(member, MemberMeta) and member.name in self._member_names_
  
  def __iter__(self):
    return self._members_.__iter__()

  def __len__(self):
    return len(self._members_)

  def __reversed__(self):
    return reversed(self._members_.__iter__())

    
class MembersMeta(type):
  def __new__(metacls, cls, bases, classdict ):
    cls_instance = super().__new__(metacls, cls, bases+(Members,), classdict)
    instance = classdict['instance']
    cls_instance._members_ = []
    member_names = set(classdict['names'])
    for name in member_names:
      member = MemberMeta( 'Member', (), {'instance' : instance, 'name' : name } )
      setattr( cls_instance, name, member )
      cls_instance._members_.append(member)
    
    cls_instance._member_names_ = member_names
    return cls_instance
  
  def __contains__(self, member):
    return isinstance(member, Member) and member.name in self._member_names_
  
  def __iter__(self):
    return self._members_.__iter__()

  def __len__(self):
    return len(self._members_)

  def __reversed__(self):
    return reversed(self._members_.__iter__())
    
class MorphMeta(type):  
  def __prepare__(metacls, cls):
    return enum._EnumDict()

  def __new__(metacls, cls, bases, classdict):
    cls_instance = super().__new__(metacls, cls, bases, classdict)
    try:
      annotations = classdict['__annotations__'] # TODO: implementacja custom morph przez annotations?
    except KeyError:
      annotations = {}
    members = [ name for name,value in classdict.items() 
                  if name in annotations or name in classdict._member_names ]
    
    cls_instance.members = [] # to properly initailize member.terminal
    cls_instance.members = MembersMeta( 'Members', (), {'instance' : cls_instance, 'names' : members } )
    return cls_instance

  def __repr__(cls):
    return "<Morph %r>" % cls.__name__
  
class Morph(metaclass=MorphMeta):
  def __init__( self, data ): 
    self.members = None # to properly initialize member.terminal
    self.members = type(self).members(self)
    for member in self.members:
      member.value = data[type(member)]

def morphism( type_, f ):
  class Morphing(type_):
    def __call__( self, *args, **kwargs ):
      return f(self, *args, **kwargs)
    def __repr__( self ):
      return super().__repr__() + 'M'
    # TODO : comparison injection
    # for equality comparisons in conflicts
    def __eq__( self, other ):
      return isclose(self,other, abs_tol=0.0001)
    def __ne__(self,other):
      return not isclose(self,other, abs_tol=0.0001)
  return Morphing