from hydra.classes import Morph, AttributeMeta
from hydra.iteration import post_order, breadth_first
from collections import Counter

def update( value, data, *args ):
  cls = type(value)
  guard(data)
  decomposed = { type(attr) : attr.value for attr in breadth_first(value) if attr.terminal }
  # print('decomposed ',decomposed)
  result = None
  conflicts = {None}
  attempt = {}
  while len(conflicts) > 0:
    attempt = dict(decomposed)
    attempt.update(data)
    
    result, solve_conflicts = solve(cls, attempt, *args)
    conflicts = { attribute for pair in solve_conflicts
                              for conflict in pair 
                                for attribute in breadth_first(conflict.instance) if attribute.terminal }
    # print('solve_conflicts ',solve_conflicts)
    # print('conflicts ',conflicts)
    decomposed = { key : value for key,value in decomposed.items() if key not in conflicts }
    # print('decomposed ',decomposed)
  return result, attempt
  
''' Builds cls instance from data dict using *args
    returns None in case of failure, uses morph to extend the amount of data
    mutates data by adding intermediate morphism results
'''
def solve( cls, data, *args ):
  # assure proper type assignment and decomposition
  guard(data)
  conflicts = []
  created = list(data.items())
  post_order_composites = list( attr for attr in post_order(cls) if not attr.terminal)
  result = None
  
  ''' Iteratively morphs the data and tries to construct higher-order classes
      Assures object equality through morph, but not identity in case of internal shared variables ''' 
  
  while len(created) > 0:
    # morph the created items, push them to data
    conflicts.extend( morph( data, *args, stack=created ) )
    # see if it's possible to build cls
    if all( member in data for member in cls.attr ):
       break
    # traverse cls, create members that are available
    created.extend( (attr, attr.value(data)) for attr in post_order_composites 
                      if attr not in data 
                        and all( member in data for member in attr.value.attr ) )
  else:
    # morph was exhausted, but and it's not possible to build cls
    # print( next( attr for attr in breadth_first(cls) if attr in data ) )
    return None, conflicts
  
  # just the terminals and non-hydra items
  new_data = { attr : value for attr,value in data.items() if attr not in post_order_composites }
  # types that occur multiple times in post_order_composites
  compositeCounter = Counter( attr.value for attr in post_order_composites )
  shared_types = { type for (type,c) in compositeCounter.items() if c > 1 }
  # type -> object mapping for shared objects
  shared_objects = {}
  # iterating in the post order so that
  # object dependency during construction is satisfied
  for attr in post_order_composites:
    attrType = attr.value
    if attrType in shared_types:
      if attrType not in shared_objects:
        shared_objects[attrType] = attrType(new_data)
      new_data[attr] = shared_objects[attrType]
    else:  
      new_data[attr] = attrType(new_data) 
  
  result = cls(new_data)
  data.clear()
  data.update(new_data) # update the data
    
  return result, conflicts 
          
def guard( values ):
  # make sure that each value has the type declared by its associated member
  values.update( (attribute, attribute.value(value)) for attribute,value in values.items() 
                    if isinstance(attribute,AttributeMeta) and type(value) != attribute.value )
  # decompose the values that are of type Morph
  values.update( (type(attribute), attribute.value) 
                    for key,value in values.items() if isinstance(value,Morph)
                      for attribute in breadth_first(value) )

''' Runs the morphisms of the data until no new results are available
    Recursively breaks each result to its constituent members and morphs them as well
    Checks inner consistency of results with data, returns the list of inconsistencies
    Morphisms have to be deterministic, their arguments are f( assigned member, *args )
    Mutates data by adding new results obtained in the process and the contents of the stack
'''
def morph( data, *args, stack=None ):
  if stack is None:
    stack = list(data.items())
  conflicts = []
  
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
      conflicts.extend( (source, key) for key,value in results.items() 
                          if data.get(key,value) != value )
                          # and key not in breadth_first(source)
      stack.extend( (target,result) for target,result in results.items() if target not in data )
      # source has been processed consistently, update the data dict
      data.update( results )
    else:
      pass # source does not encode transformation, so skip it
    data[source] = value
  return conflicts
  
