from hydra.classes import Morph, AttributeMeta
from hydra.iteration import post_order, breadth_first
from collections import Counter



def update( value, data, *args ):
  cls = type(value)
  guard(data)
  # decompose value down to terminals
  decomposed_value = { type(attr) : attr.value for attr in breadth_first(value) if attr.terminal }
  # decompose each element in data down to terminals
  decomposed_data = { type(value_attr).value : value_attr.value 
                        for key,value in data.items() if isinstance(key, AttributeMeta) and isinstance( value, Morph )
                          for value_attr in breadth_first(value) if value_attr.terminal }
  decomposed_data.update( (key, value) for key,value in data.items() if not isinstance(key, AttributeMeta) or not isinstance( value, Morph ) )
  print('decomposed_data in ', decomposed_data)
  # for all composite types in cls
  # mapping of type -> set of type's terminal dependencies
  dependencies = { type_attr.value : { dec_attr for dec_attr in breadth_first(type_attr.value) if dec_attr.terminal } 
                                        for type_attr in breadth_first(cls) if not type_attr.terminal }
  
  result = None
  conflicts = {None}
  attempt = {}
  
  while len(conflicts) > 0:
    # overwrite decomposed_value with decomposed_data
    attempt = dict(decomposed_value)
    attempt.update(decomposed_data)
    # try building result
    result, solve_conflicts, shared = solve(cls, attempt, *args)
    # decompose shared values down to terminals
    shared_terminals = { attr for item in shared for attr in dependencies[item] }
    # decompose each source to terminals that are not present in shared_terminals
    '''conflicts = { attribute for source in (solve_conflicts & dependencies.keys())
                              for attribute in (dependencies[source] - shared_terminals) }'''
    conflicts = { attribute for source in solve_conflicts if source.value in dependencies
                                    for attribute in dependencies[source.value] if attribute not in shared_terminals }
    conflicts.update( shared_terminal for source in (conflicts & shared.keys())
                                        for shared_terminal in dependencies[source] )
    conflicts.update( solve_conflicts )
    # remove conflicts from decomposed_value
    decomposed_value = { key : value for key,value in decomposed_value.items() if key not in conflicts }
    print('decomposed_value ', decomposed_value)
    print('decomposed_data ', decomposed_data)
    print('solve_conflicts ', solve_conflicts )
    print('conflicts ', conflicts )
    input()
    
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
    created.extend( (type_attr, type_attr.value(data)) for type_attr in post_order_composites 
                        if type_attr not in data 
                          and all( member in data for member in type_attr.value.attr ) )
  
  ''' At this stage, data is constructed, but it may contain multiple copies of an object
      that satisfies the class' == operator. Since all objects need to be decomposible
      to unique set of attribute : value pairs (data is a dict), these copies are actually one object.
      We need to make sure that the hierarchy contains only one object of each type. '''
  
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
  return result, conflicts, shared_composites
          
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
  conflicts = set()
  
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
      conflicts.update( source for key,value in results.items() 
                                if data.get(key,value) != value )
      stack.extend( (target,result) for target,result in results.items() if target not in data )
      # source has been processed consistently, update the data dict
      data.update( results )
    else:
      pass # source does not encode transformation, so skip it
    data[source] = value
  return conflicts
  
