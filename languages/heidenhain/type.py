import enum
from math import isclose

class Member:
  __slots__ = 'instance', 'name'
  def __init__(self, instance, name):
    object.__setattr__(self,'instance', instance)
    object.__setattr__(self,'name',   name )
    
  def get( self ):
    return getattr( self.instance, self.name )
  
  def set( self, value ):
    return setattr( self.instance, self.name, value )
    
  def __setattr__( self, name, value ):
    raise AttributeError('Cannot reassign Member values')
    
  def __delattr__( self, attr ):
    raise AttributeError('Cannot delete Member values')
    
  def __repr__( self ):
    return '%s.%s' % (self.instance, self.name)

class Members:
  def __init__( self, instance, names ):
    self._members_ = []
    member_names = set(names)
    for name in member_names:
      member = Member( instance, name )
      setattr( self, name, member )
      self._members_.append(member)
    
    self._member_names_ = member_names
  
  def __contains__(self, member):
    return isinstance(member, Member) and member.name in self._member_names_
  
  def __delattr__(self, attr):
    if attr in cls._member_names_:
        raise AttributeError(
                "%s: cannot delete Morph member." % cls.__name__)
    super().__delattr__(attr)

  def __dir__(self):
    return (['__class__', '__doc__', '__members__', '__module__'] +
            list(self._member_names_))

  def __iter__(self):
    return self._members_.__iter__()

  def __len__(self):
    return len(self._members_)

  def __reversed__(self):
    return reversed(self._members_.__iter__())

  def __setattr__(self, name, value):
    members = self.__dict__.get('_member_names_', [])
    if name in members:
      raise AttributeError('Cannot reassign Morph members.')
    super().__setattr__(name, value)  

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
    cls_instance.members = Members( cls_instance, members )
    return cls_instance

  def __delattr__(cls, attr):
    if attr == 'members' or attr in cls.members._member_names_:
        raise AttributeError("%s: cannot delete Morph member." % cls.__name__)
    super().__delattr__(attr)

  def __repr__(cls):
    return "<Morph %r>" % cls.__name__

  def __setattr__(cls, name, value):
    members = cls.__dict__.get('members', None)
    if members is not None and ( name in members._member_names_ or name == 'members' ):
      raise AttributeError('Cannot reassign Morph members.')
    super().__setattr__(name, value)  
    
class Morph(metaclass=MorphMeta):
  def __init__( self, data ):
    self.members = Members( self, ( member.name for member in type(self).members ) )
    for member in type(self).members:
      setattr( self, member.name, data[member] )

def in_order( cls ):
  stack = [ member for member in cls.members ]
  while len(stack) > 0:
    member = stack.pop(-1)
    value = member.get()
    if not visited and hasattr(value, 'members'):
      stack.extend( mem for mem in value.members )
      continue
    yield member

def post_order( cls ):
  stack = [ (member, False) for member in cls.members ]
  while len(stack) > 0:
    member, visited = stack.pop(-1)
    value = member.get()
    if not visited and hasattr(value, 'members'):
      stack.append( (member, True) ) 
      stack.extend( (mem, False) for mem in value.members )
      continue
    yield member

''' Performs breadth-first traversal
'''
def breadth_first( obj ):
  stack = [ member for member in obj.members ]
  yield from stack
  while len(stack) > 0:
    stack = [ bottom_item 
                for top_item in stack if hasattr( top_item.get(), 'members')
                  for bottom_item in top_item.get().members ]
    yield from stack
    

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
    if all( member in data for member in cls.members ):
       result = cls( data )
       break
    # traverse cls, create members that are available
    created.extend( (key, key.get()(data)) for key in traversal 
                      if issubclass(key.get(), Morph)
                        and key not in data 
                        and all( member in data for member in key.get().members ) )
    
          
  return result, conflicts 
          
def guard( values ):
  # make sure that each value has the type declared by its associated member
  values.update( (key, key.get()(value)) for key,value in values.items() 
                    if isinstance(key,Member) and type(value) != key.get() )
  # decompose the values that are of type Morph
  values.update( (member, member.get()) 
                    for key,value in values.items() if isinstance(value,Morph)
                      for member in breadth_first(value) )

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