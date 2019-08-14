from hydra.classes import Morph, AttributeMeta
from hydra.iteration import post_order_cached, breadth_first, breadth_first_cached
from collections import Counter

  
def update( val, data, *args, limit=10 ):
  cls = type(val)
  dependencies = cached_dependencies(cls)
  guard(data)
  # decompose value down to terminals
  decomposed_value = { type(attr) : attr.value for attr in breadth_first(val) if attr.terminal }
  # decompose each element in data down to terminals
  decomposed_data = { type(value_attr).value : value_attr.value 
                        for key,value in data.items() if isinstance(key, AttributeMeta) and isinstance( value, Morph )
                          for value_attr in breadth_first(value) if value_attr.terminal }
  decomposed_data.update( (key, value) for key,value in data.items() if not isinstance(key, AttributeMeta) or not isinstance( value, Morph ) )
  result = None
  solve_conflicts = {}
  
  for i in range(limit):
    # overwrite decomposed_value with decomposed_data
    attempt = dict(decomposed_value)
    attempt.update(decomposed_data)
    # try building result
    result, solve_conflicts = solve(cls, attempt, *args)
    if len(solve_conflicts) == 0:
      return result
    # for each source,target pair of conflict, add the terminal decomposition of target, 
    # but omit the terminals that are shared between them.
    conflicts = { attribute for source,target in solve_conflicts if target.value in dependencies
                              for attribute in ( dependencies[target.value] - dependencies.get(source.value,[]) ) }
    # append the terminals
    conflicts.update( target for source,target in solve_conflicts )
    # remove conflicts from decomposed_value
    decomposed_value = { key : value for key,value in decomposed_value.items() if key not in conflicts }

    
  raise RuntimeError('Update iteration limit reached') 

  
''' Builds cls instance from data dict using *args
    returns None in case of failure, uses morph to extend the amount of data
    mutates data by adding intermediate morphism results
'''
def solve( cls, data, *args ):
  # guard(data)
  conflicts = []
  created = list(data.items())
  post_order_composites = set( attr for attr in post_order_cached(cls) if not attr.terminal)
  
  ''' Iteratively morphs the data and tries to construct higher-order classes
      Assures object equality through morph, but not identity in case of internal shared variables '''   
  while len(created) > 0:
    # morph the created items, push them to data
    conflicts.extend( morph( data, *args, stack=created ) )
    # post_order_composites = post_order_composites - data.keys()
    # traverse cls, create members that are available        
    for type_attr in post_order_composites:
      if type_attr not in data and all( member in data for member in type_attr.value.attr ):
        created.append( (type_attr, type_attr.value(data)) )
  
  ''' At this stage, data is constructed, but it may contain multiple copies of an object
      that is composed of the same terminals. Since all objects need to be decomposible
      to unique set of attribute : value pairs (data is a dict), these copies are actually one object.
      We need to make sure that the hierarchy contains only one object of each type. '''
  
  if len(conflicts) == 0:
    data_composites = [ (type_attr, value) for type_attr,value in data.items() 
                                            if isinstance(type_attr,AttributeMeta) and not type_attr.terminal ]
    type_count = Counter( type_attr.value for type_attr,value in data_composites )
    # type -> object mapping for shared objects
    shared_composites = { type_attr.value : value
                            for type_attr,value in data_composites
                              if type_count[type_attr.value] > 1 }
    # update the value of the attribute to its shared state
    for type_attr, value in data_composites:
      for shared_attr in value.attr:
        value_type = type(shared_attr).value
        if value_type in shared_composites:
          shared_attr.value = shared_composites[value_type]
  
  result = cls(data) if all( attr in data for attr in cls.attr ) else None
  return result, conflicts
  
''' Runs the morphisms of the data until no new results are available
    Recursively breaks each result to its constituent members and morphs them as well
    Checks inner consistency of results with data by class' operator !=, returns the list of conflicts
    Morphisms have to be deterministic, their arguments are f( assigned member, *args )
    Mutates data by adding new results obtained in the process and the contents of the stack
'''
def morph( data, *args, stack=None ):
  if stack is None:
    stack = list(data.items())
  conflicts = []
  # morph the stack contents
  while len(stack) > 0:
    # Get source and value from stack
    source, value = stack.pop(-1)
    
    if callable( value ):
      # call the morphism
      results = value( source, *args )
      if any( key.instance is not source.instance for key in results ):
        error = ( 'Result key:%s, key.instance:%s' % (key,key.instance) 
                    for key in results if key.instance is not source.instance )
        raise RuntimeError(
        'Morphisms have to return keys that belong to the same Morph as source\nSource:%s, source.instance:%s\n' % 
         (source, source.instance) + '\n'.join( error ) )
      
      results_to_process = list(results.items())
      while len(results_to_process) > 0:
        target, result = results_to_process.pop()
        # assure that the type of value equals the one declared in target
        if target.value != type(result):
          results[target] = target.value(result)
        else:
          results[target] = result
        if target.terminal:
          # conflict checking
          if data.get(target,result) != result:
            conflicts.append( (source, target) )
        else:
          # composites are in conflict if their terminals are in conflict
          # no need to check the intermediate composites
          for val_attr in breadth_first(result):
            type_  = type(val_attr)
            value_ = val_attr.value
            if val_attr.terminal and data.get(type_,value_) != value_:
              conflicts.append( (source, target) )
              break
              
      stack.extend( (target,result) for target,result in results.items() if target not in data )
      data.update( results )
    else:
      pass # source does not encode transformation, so skip it
    data[source] = value
  return conflicts
  
          
def guard( values ):
  # make sure that each value has the type declared by its associated member
  values.update( (attribute, attribute.value(value)) for attribute,value in values.items() 
                    if isinstance(attribute,AttributeMeta) and type(value) != attribute.value )
  # decompose the values that are of type Morph
  values.update( (type(attribute), attribute.value) 
                    for key,value in values.items() if isinstance(value,Morph)
                      for attribute in breadth_first(value) )

_dependencies_ = {}

def cached_dependencies( cls ):
  if cls in _dependencies_:
    return _dependencies_
  _dependencies_[cls] = set()
  # for all composite types in cls
  # mapping of type -> set of type's terminal dependencies
  # TODO : optimize the nested breadth_first? 
  for type_attr in breadth_first_cached(cls):
    if not type_attr.terminal:
      if type_attr.value not in _dependencies_:
        _dependencies_[ type_attr.value ] = { dec_attr for dec_attr in breadth_first_cached(type_attr.value) if dec_attr.terminal }
      _dependencies_[cls].update( _dependencies_[ type_attr.value ] )
  return _dependencies_

def construct( cls, data ):
  post_order_composites = ( attr for attr in post_order_cached(cls) if not attr.terminal)
  for type_attr in post_order_composites:
    if type_attr not in data and all( member in data for member in type_attr.value.attr ):
      data[type_attr] = type_attr.value(data)
  return cls(data)