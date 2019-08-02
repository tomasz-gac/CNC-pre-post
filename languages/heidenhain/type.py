import enum
from math import isclose

class Member:
  __slots__ = 'cls', 'name', 'type'
  def __init__(self, cls, name, type_):
    if isinstance( type_, Member ) or (hasattr(cls, name) and getattr(cls, name) != type_):
      raise RuntimeError('Cannot manually create instances of Member')
    object.__setattr__(self,'cls', cls)
    object.__setattr__(self,'name',   name )
    object.__setattr__(self,'type',   type_ )
    
  def __setattr__( self, name, value ):
    raise AttributeError('Cannot reassign Member values')
    
  def __delattr__( self, attr ):
    raise AttributeError('Cannot delete Member values')
    
  def __repr__( self ):
    return '%s.%s:%s' % (self.cls.__name__, self.name, self.type.__name__)

class MorphMeta(type):  
  def __prepare__(metacls, cls):
    return enum._EnumDict()

  def __new__(metacls, cls, bases, classdict):
    cls_instance = super().__new__(metacls, cls, bases, classdict)
    cls_instance._members_ = []
    try:
      annotations = classdict['__annotations__'] # TODO: implementacja custom morph przez annotations?
    except KeyError:
      annotations = {}
    for name,type_ in classdict.items():
      # enum._EnumDict fails to detect functions assigned as enum values,
      # use annotations instead
      if name in annotations or name in classdict._member_names:
        member = Member( cls_instance, name, type_ )
        setattr( cls_instance, name, member )
        cls_instance._members_.append((member,type_))
    cls_instance._member_names_ = classdict._member_names
    return cls_instance
  
  def __contains__(cls, member):
    return isinstance(member, Member) and member.name in cls._member_names_

  def __delattr__(cls, attr):
    if attr in cls._member_names_:
        raise AttributeError(
                "%s: cannot delete Morph member." % cls.__name__)
    super().__delattr__(attr)

  def __dir__(self):
    return (['__class__', '__doc__', '__members__', '__module__'] +
            list(self._member_names_.keys()))

  def __iter__(cls):
    return cls._members_.__iter__()# (cls._member_map_[name] for name in cls._member_names_)

  def __len__(cls):
    return len(cls._members_)

  def __repr__(cls):
    return "<Morph %r>" % cls.__name__

  def __reversed__(cls):
    return reversed(cls._members_.__iter__())

  def __setattr__(cls, name, value):
    members = cls.__dict__.get('_member_names_', [])
    if name in members:
      raise AttributeError('Cannot reassign Morph members.')
    super().__setattr__(name, value)  
    
class Morph(metaclass=MorphMeta):
  def __init__( self, data ):
    self._members_ = [(member,data[member]) for member,t in type(self)]
    for member,t in type(self):
      setattr( self, member.name, data[member] )
      
  def __contains__(self, member):
    return isinstance(member, Member) and member.name in type(self)._member_names_

  def __delattr__(self, attr):
    if attr in type(self)._member_names_:
        raise AttributeError(
                "%s: cannot delete Morph member." % type(self).__name__)
    super().__delattr__(attr)

  def __dir__(self):
    return (['__class__', '__doc__', '__members__', '__module__'] +
            list(self._member_names_.keys()))

  def __iter__(self):
    return self._members_.__iter__()

  def __len__(self):
    return len(self._members_)

  def __reversed__(cls):
    return reversed(self._members_.__iter__())

def post_order( cls ):
  stack = [ (member, value, False) for member,value in cls ]
  while len(stack) > 0:
    member, value, visited = stack.pop(-1)
    if not visited and issubclass( member.type, Morph ):
      stack.append( (member, value, True) ) 
      stack.extend( (mem,v, False) for mem,v in value )
      continue
    yield member, value 

def post_order_obj( obj ):
  stack = [ (member, getattr(value,member.name),False) for member in reversed(type(obj)) ]
  while len(stack) > 0:
    source, value, visited = stack.pop(-1)
    if not visited and issubclass( source.type, Morph ):
      stack.append( (source, value, True) ) 
      stack.extend( (member, getattr(value,member.name),False) for member in reversed(type(value)) )
      continue
    yield source, value

''' Performs breadth-first traversal
'''
def breadth_first_obj( obj ):
  stack = [ (member,getattr( obj, member.name )) for member, in type(obj) ]
  while len(stack) > 0:
    member, current = stack.pop(-1)
    if isinstance( current, Morph ):
      l = len(stack)
      stack.extend( (member,getattr( current, member.name )) for member, in type(current) )
      yield from stack[l:]

''' Builds cls instance from data dict using *args
    returns None in case of failure, uses morph to extend the amount of data
    mutates data by adding intermediate morphism results
'''
def solve( cls, data, *args, traversal=post_order ):
  # assure proper type assignment and decomposition
  guard(data)
  conflicts = []
  created = list(data.items())
  traversal = list( traversal(cls) )
  result = None
  
  while len(created) > 0:
    # morph the created items, push them to data
    conflicts.extend( morph( data, *args, stack=created ) )
    
    # try building cls
    if all( member in data for member,value in cls ):
       result = cls( data )
       break
    # traverse cls, create members that are available
    created.extend( (key, key.type(data)) for key,value in traversal 
                      if issubclass(value, Morph)
                        and key not in data 
                        and all( member in data for member,value in key.type ) )
    
          
  return result, conflicts 
          
def guard( values ):
  # make sure that each value has the type declared by its associated member
  values.update( (key, key.type(value)) for key,value in values.items() 
                    if isinstance(key,Member) and type(value) != key.type )
  # decompose the values that are of type Morph
  values.update( item for key,value in values.items() if isinstance(value,Morph)
                        for item in breadth_first_obj(value) )

''' Runs the morphisms of the data until no new results are available
    Recursively breaks each result to its constituent members and morphs them as well
    Checks inner consistency of results with data, returns the list of inconsistencies
    Morphisms have to be deterministic, their arguments are f( assigned member, *args )
    Mutates data by adding new results obtained in the process and the contents of the stack
'''
def morph( data, *args, stack=None ):
  if stack is None:
    stack = list(data.items())
  inconsistent = []
  
  # morph the values contents
  while len(stack) > 0:
    # Get source and value from values
    source, value = stack.pop(-1)
    
    if callable( value ):
      # call the morphism
      results = value( source, *args )
      # assure proper type assignment and decomposition
      guard( results )
      # get the value inconsistencies between data and results
      inconsistent.extend( (source, key) for key,value in results.items() if data.get(key,value) != value )      
      stack.extend( (target,result) for target,result in results.items() if target not in data )
      # source has been processed consistently, update the data dict
      data.update( results )
    else:
      pass # source does not encode transformation, so skip it
    data[source] = value
  return inconsistent
  
def morphism( type_, f ):
  class Morphing(type_):
    def __call__( self, *args, **kwargs ):
      return f(self, *args, **kwargs)
    def __repr__( self ):
      return super().__repr__() + 'M'
      
    def __eq__( self, other ):
      return isclose(self,other, abs_tol=0.0001)
    def __ne__(self,other):
      return not isclose(self,other, abs_tol=0.0001)
  return Morphing