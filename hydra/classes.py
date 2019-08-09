import enum
from math import isclose
from collections import Counter
from hydra.iteration import breadth_first

class Attribute:
  __slots__ = 'instance', 'name'
  def __init__( self, instance, name ):
    self.instance = instance
    self.name     = name
    self.terminal = not hasattr(getattr(instance,name), 'attr')
  
  # This has to be a property because Members serve as keys
  # and their value cannot take part in hashing
  @property
  def value( self ):
    return getattr( self.instance, self.name )
    
  @value.setter
  def value( self, value ):
    setattr( self.instance, self.name, value )
    
  def __repr__( self ):
    return '%s.%s' % (self.instance, self.name)    


class AttributeMeta(type):
  __slots__ = 'instance', 'name'
  def __new__(metacls, cls, bases, classdict ):
    cls_instance = super().__new__(metacls, cls, bases+(Attribute,), classdict)
    cls_instance.instance = classdict['instance']
    cls_instance.name = classdict['name']
    cls_instance.terminal = not hasattr(getattr(cls_instance.instance,cls_instance.name), 'attr')
    return cls_instance
    
  # This has to be a property because Members serve as keys
  # and their value cannot take part in hashing
  @property
  def value( self ):
    return getattr( self.instance, self.name )
    
  @value.setter
  def value( self, value ):
    setattr( self.instance, self.name, value )
    
  def __repr__( self ):
    return '%s.%s' % (self.instance, self.name)    

class Attributes:
  def __init__( self, instance ):
    self._attributes_ = []
    for attrType in type(instance).attr:
      attr = attrType(instance, attrType.name)
      setattr( self, attr.name, attr )
      self._attributes_.append(attr)
    
    self._attribute_names_ = { attr.name for attr in self._attributes_ }
  
  def __contains__(self, attr):
    return isinstance(attr, AttributeMeta) and attr.name in self._attribute_names_
  
  def __iter__(self):
    return self._attributes_.__iter__()

  def __len__(self):
    return len(self._attributes_)

  def __reversed__(self):
    return reversed(self._attributes_.__iter__())

    
class AttributesMeta(type):
  def __new__(metacls, cls, bases, classdict ):
    cls_instance = super().__new__(metacls, cls, bases+(Attributes,), classdict)
    instance = classdict['instance']
    # base inheritance is handled by type(), but iteration is not.
    # remove duplicates while preserving order
    seen = set()
    cls_instance._attributes_ = [attr for base in bases 
                                        for attr in base 
                                          if not (attr in seen or seen.add(attr))]
    attribute_names = set(classdict['names'])
    for name in attribute_names:
      attr = AttributeMeta( 'Attribute', (), {'instance' : instance, 'name' : name } )
      setattr( cls_instance, name, attr )
      cls_instance._attributes_.append(attr)
    
    cls_instance._attribute_names_ = attribute_names
    return cls_instance
  
  def __contains__(self, attr):
    return isinstance(attr, Member) and attr.name in self._attribute_names_
  
  def __iter__(self):
    return self._attributes_.__iter__()

  def __len__(self):
    return len(self._attributes_)

  def __reversed__(self):
    return reversed(self._attributes_.__iter__())

    
class MorphMeta(type):  
  def __prepare__(metacls, cls):
    return enum._EnumDict()

  def __new__(metacls, cls, bases, classdict):
    cls_instance = super().__new__(metacls, cls, bases, classdict)
    try:
      annotations = classdict['__annotations__'] # TODO: implementacja custom morph przez annotations?
    except KeyError:
      annotations = {}
    attributes = [ name for name,value in classdict.items() 
                    if name in annotations or name in classdict._member_names ]
    attr_bases = tuple( base.attr for base in bases if hasattr(base, 'attr')  )
    cls_instance.attr = None # to properly initailize attribute.terminal
    cls_instance.attr = AttributesMeta( 'Attributes', attr_bases, {'instance' : cls_instance, 'names' : attributes } )
    return cls_instance

  def __repr__(cls):
    return "<Morph %r>" % cls.__name__
  
class Morph(metaclass=MorphMeta):
  def __init__( self, data ): 
    self.attr = None # to properly initialize Attribute.terminal
    self.attr = type(self).attr(self)
    for attr in self.attr:
      attr.value = data[type(attr)]
    
  def __eq__( self, other ):
    raise RuntimeError('Morph.__eq__')
    # return all( lhs.value == rhs.value for lhs,rhs in zip(self.attr,other.attr) )
    
  def __ne__( self, other ):
    raise RuntimeError('Morph.__ne__')
    # return any( lhs.value != rhs.value for lhs,rhs in zip(self.attr,other.attr) )
    
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