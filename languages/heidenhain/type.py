import enum

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
    cls_instance._member_names_ = classdict._member_names
    cls_instance._member_map_  = {}
    try:
      annotations = classdict['__annotations__'] # TODO: implementacja custom morph przez annotations?
    except KeyError:
      annotations = {}
    for name,type_ in classdict.items():
      # enum._EnumDict fails to detect functions assigned as enum values,
      # use annotations instead
      if name in annotations or name in cls_instance._member_names_:
        value = Member( cls_instance, name, type_ )
        setattr( cls_instance, name, value )
        cls_instance._member_map_[name] = value
    return cls_instance
  
  def __contains__(cls, member):
    return isinstance(member, Member) and member.name in cls._member_map_

  def __delattr__(cls, attr):
    if attr in cls._member_map_:
        raise AttributeError(
                "%s: cannot delete Morph member." % cls.__name__)
    super().__delattr__(attr)

  def __dir__(self):
    return (['__class__', '__doc__', '__members__', '__module__'] +
            self._member_names_)

  def __getitem__(cls, name):
    return cls._member_map_[name]

  def __iter__(cls):
    return (cls._member_map_[name] for name in cls._member_names_)

  def __len__(cls):
    return len(cls._member_names_)

  def __repr__(cls):
    return "<Morph %r>" % cls.__name__

  def __reversed__(cls):
    return (cls._member_map_[name] for name in reversed(cls._member_names_))

  def __setattr__(cls, name, value):
    member_map = cls.__dict__.get('_member_map_', {})
    if name in member_map:
      raise AttributeError('Cannot reassign Morph members.')
    super().__setattr__(name, value)
    

class Morph(metaclass=MorphMeta):
  def __init__( self, data ):
    for member in list(type(self)):
      setattr( self, member.name, data[member] )
  
  ''' Builds cls instance from data dict using *args
      returns None in case of failure, uses morph and dismember to extend the amount of data
      mutates data by adding intermediate morphism results
  '''
  @classmethod
  def solve( cls, data, *args ):
    instance = cls.__new__(cls)
    members = list(cls)
    skipped = []
    while True:
      # Try to find data for each declared member
      for member in members:
        value  = None
        try:
          value = data[member]
        except KeyError:
          # no member data, try to construct recursively
          try:
            value = member.type.solve(data, *args) # returns None on failure
          except AttributeError: # The class does not support Morph interface
            pass
          if value is None:
            skipped.append(member)
          else:
            data[member] = value
        # if there was no member in data and it was obtained by type.solve,
        # but the solve failed - it is safe to assign the value
        # because member was added to skipped and will either be re-iterated, or discarded
        setattr(instance, member.name, value)
      
      if len(skipped) > 0:
        # morph the data to see if anything new appears
        dataCount = len(data)
        morph( data, *args )
        if dataCount < len(data):
          members = skipped
          skipped = []
        else:
          return None
      else:
        return instance
    
    
def consistence( values, data ):
  if any( data.get(key, value) != value for key,value in values.items() ):
    inconsistent = { key : value for key,value in values.items() if data.get(key, value) != value }
    error = ''
    for key,value in inconsistent.items():
      error = '(values[%s]=%s) != (data[%s]=%s)\n' % (key,value,key,data[key])
    # if any key : value pair from values is inconsistent with key : value pair from data,
    raise RuntimeError('Inconsistent input data during Morph decompose:\n'+error) # raise an error
    
''' Checks consistency of key:value pairs of values with data
    if value is a Morph, recursively breaks it down to members and checks their consistency aswell
    returns a dict of key:value pairs that were broken down
    throws RuntimeError in case of inconsistency
'''
def decompose( values, data = None ):
  if data is None:
    data = dict(values)
  else:
    consistence( values, data )
  
  # for each item in values, see if it is derived from Morph
  # drop the key of that value and break it down to its constituent members
  # store the pair member : value.member in the values
  values = {
    member : getattr( value, member.name )
      for value in values.values() if isinstance( value, Morph )
        for member in list(type(value))
    }
  
  # recursion termination
  if len(values) == 0:
    return {}
  else:
    consistence( values, data )    
    # perform recursion - pass the values for further dismemberment
    # update the newly created values and return them
    values.update( decompose( values, data ) )
    return values
        
''' Runs the morphisms of the data until no new results are available
    Recursively breaks each result to its constituent members and morphs them as well
    Checks inner consistency of results with data, throws RuntimeError in case of inconsistent results
    Morphisms have to be deterministic, their arguments are f( assigned member, *args )
    Mutates data by adding new results obtained in the process
'''
def morph( values, *args, data = None ):
  if data is None:
    values.update( decompose( values ) )
    data = dict(values)
  else:
    values.update( decompose( values, data ) )
  # morph the values contents
  while len(values) > 0:
    # Get source and value from values
    source, value = values.popitem()
    try:
      # if type is inconsistent with declaration, try to convert it
      if type(value) != source.type:
        values[source] = value = source.type(value)
    except AttributeError:
      # source does not support Morph interface
      pass
    
    if callable( value ):
      # call the morphism
      results = value( source, *args )
      # recursively decompose the results and check consistency with data
      # throws RuntimeError on consistency failure
      results.update( decompose( results, data ) )
      # update the values with newly created items
      values.update( { target : result for target,result in results.items() if target not in data } )
      # source has been processed consistently, update the data dict
      data.update( results )
    else:
      continue # source does not encode transformation, so skip it
  # push the processed results back to values
  values.update( data )
  
def morphism( type, f ):
  class Morphing(type):
    def __call__( self, *args, **kwargs ):
      return f(self, *args, **kwargs)
    def __repr__( self ):
      return '<Morphing(%s) : %s>' % (type,f)
  return Morphing