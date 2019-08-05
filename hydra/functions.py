from hydra.classes import Morph, AttributeMeta
from hydra.iteration import post_order, breadth_first

def update( value, data, *args ):
  cls = type(value)
  guard(data)
  decomposed = { type(attr) : attr.value for attr in breadth_first(value) if attr.terminal }
  print('decomposed ',decomposed)
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
    print('solve_conflicts ',solve_conflicts)
    print('conflicts ',conflicts)
    decomposed = { key : value for key,value in decomposed.items() if key not in conflicts }
    print('decomposed ',decomposed)
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
  traversal = list( post_order(cls) )
  result = None
  
  while len(created) > 0:
    # morph the created items, push them to data
    conflicts.extend( morph( data, *args, stack=created ) )
    
    # try building cls
    if all( member in data for member in cls.attr ):
       result = cls( data )
       break
    # traverse cls, create members that are available
    created.extend( (key, key.value(data)) for key in traversal 
                      if issubclass(key.value, Morph)
                        and key not in data 
                        and all( member in data for member in key.value.attr ) )
    
          
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
  
