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
    return '<Member %r.%s of type %r>' % (self.cls, self.name, self.type)

class MorphMeta(type):  
  def __prepare__(metacls, cls):
    return enum._EnumDict()

  def __new__(metacls, cls, bases, classdict):
    cls_instance = super().__new__(metacls, cls, bases, classdict)
    cls_instance._member_names_ = classdict._member_names
    cls_instance._member_map_  = {}
    try:
      annotations = classdict['__annotations__']
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
    

class MorphInitFailedException(Exception):
  pass
    
class Morph(metaclass=MorphMeta):
  ''' Throws MorphInitFailedException on failure,
      see construct for details
  '''
  def __init__( self, data ):
    instance = type(self).construct( data, self=self )
    if instance is None:
      raise MorphInitFailedException('Missing argument for %r __init__' % (type(self))) from None
  
  def morph( self, update, *args ):
    result = {}
    for member in type(self):
      result.update( getattr( self, member.name ).morph( update, *args ) )
    if callable(self):
      result.update( self( update, *args ) )
    return result
    
  ''' Tries to initialize class instance using data dict
      when no direct members are present, tries to construct them recursively
      Does not call .morph, use .solve instead
      returns the constructed instance, or None upon failure
  '''
  @classmethod
  def construct( cls, data, self=None ):
    if self is None:
      self = cls.__new__(cls)
    # If any of the member values failed, we want to keep constructing
    # so that data is updated accordingly
    failed = False
    # Try to find data for each declared member
    for member in cls:
      value  = None
      update = None
      try:
        value = data[member]
        # if type is inconsistent with declaration, try to convert it
        if type(value) != member.type:
          value = member.type(value)
      except KeyError: 
        # no member data, try to construct recursively
        try:
          value = member.type.construct(data) # returns None on failure
        except AttributeError: # The class does not support Morph interface
          pass
        if value is None:
          failed = True
        else:
          data[member] = value
      # in case of failure, self is ignored so setting None is ok
      setattr(self, member.name, value)
    
    return self if not failed else None
    
  @classmethod
  def solve( cls, data, *args ):
    instance  = None
    processed = {}
    # assure type consistency so that .morph works
    queue  = { source : (source.type(value) if type(value) != source.type else value)
                          for source,value in data.items() }
    # instance construction loop
    while True:
      # save the processed key set for difference
      processedKeys = set(processed.keys())
      # all items in queue have been processed, try building the cls instance
      instance = cls.construct( processed )
      if instance is not None:
        break # instance constructed
      elif len(processed) != len(processedKeys):
        # instance not constructed, but new items have been constructed
        # run the morphing loop on them and try again
        queue.update(( key,value for key,value in processed if key not in processedKeys ))
      else:
        # no instance created and no new items for morphing
        break
      
      # morphing loop
      while True:
        try:
          # Get source and value from queue
          source, value = queue.popitem()
        except KeyError:
          break # No more elements to process
        # append for consistency checks in case source == target
        processed[source] = value
        
        try:
        # call the morphism
        results = value.morph( value, *args )
        except AttributeError:
          continue # does not support the Morph interface, skip it
          
        for target, result in results.items():
          # Check if result is contained in queue and processed,
          # see if the value is consistent using the == operator
          queueConsistent     = queue.get(target,result)     == result
          processedConsistent = processed.get(target,result) == result
          # Check if the target is new
          newTarget = target not in queue and target not in processed
          
          if not queueConsistent or not processedConsistent:
            # If the target is already present, raise an error if its value is inconsistent
            # It may have been added by transform function, this ensures that its inverse works properly
            raise RuntimeError('Inconsistent value for '+str(source)+':'+str(value)+'->'+str(target)+':'+str(result))
          if newTarget:
            # If target is new, add it to the queue for invariant processing
            queue[target] = result
          
        # source has been processed consistently
        # it's okay to overwrite in case when source == target
        processed.update( results )
    
    return instance
    
