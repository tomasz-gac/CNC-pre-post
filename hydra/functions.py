from hydra.classes import Morph, AttributeMeta
from hydra.iteration import post_order, breadth_first
from collections import Counter

def update( value, data, *args ):
  cls = type(value)
  guard(data)
  decomposed = { type(attr) : attr.value for attr in breadth_first(value) if attr.terminal }
  result = None
  conflicts = {None}
  attempt = {}
  while len(conflicts) > 0:
    print('-----------UPDATE START')
    attempt = dict(decomposed)
    attempt.update(data)
    
    result, solve_conflicts = solve(cls, attempt, *args)
    conflicts = { attribute for pair in solve_conflicts
                              for conflict in pair 
                                for attribute in breadth_first(conflict.instance) if attribute.terminal }
    
    decomposed = { key : value for key,value in decomposed.items() if key not in conflicts }
    print('-------UPDATE END')
  return result, attempt
  
''' Builds cls instance from data dict using *args
    returns None in case of failure, uses morph to extend the amount of data
    mutates data by adding intermediate morphism results
'''
def solve( cls, data, *args ):
  guard(data)
  conflicts = []
  created = list(data.items())
  post_order_composites = list( attr for attr in post_order(cls) if not attr.terminal)
  
  ''' Iteratively morphs the data and tries to construct higher-order classes
      Assures object equality through morph, but not identity in case of internal shared variables '''   
  while len(created) > 0:
    # morph the created items, push them to data
    conflicts.extend( morph( data, *args, stack=created ) )
    # traverse cls, create members that are available
    created.extend( (attr, attr.value(data)) for attr in post_order_composites 
                      if attr not in data 
                        and all( member in data for member in attr.value.attr ) )

  ''' At this stage, data is constructed, but it may contain multiple copies of an object
      that satisfies the class' == operator. Since all objects need to be decomposible
      to unique set of attribute : value pairs (data is a dict), these copies are actually one object.
      We need to make sure that the hierarchy contains only one object of each type. '''
  type_occurrences = Counter( type_attr.value for type_attr in post_order_composites )
  # type -> object mapping for shared objects
  shared_composites = { 
    type_attr.value : data.get(type_attr, None)
      for type_attr in post_order_composites
        if type_occurrences[type_attr.value] > 1
    }
  # decompose all composite values from data and return the attributes
  # that contain values of type that appears in shared_composites
  shared_attributes = ( shared_attr 
                          for type_attr in post_order_composites if type_attr in data
                            for shared_attr in data[type_attr].attr if type(shared_attr).value in shared_composites )
  # update the value of the attribute to its shared state
  for shared_attr in shared_attributes:
    shared_attr.value = shared_composites[ type(shared_attr).value ]
  
  result = cls(data) if all( attr in data for attr in cls.attr ) else None
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
    Checks inner consistency of results with data by class' operator !=, returns the list of conflicts
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
  
