from hydra.classes import Morph, AttributeMeta
from hydra.iteration import post_order, breadth_first
from collections import Counter

_dependencies_ = {}

def update( value, data, *args, limit=10 ):
  cls = type(value)
  guard(data)
  # decompose value down to terminals
  decomposed_value = { type(attr) : attr.value for attr in breadth_first(value) if attr.terminal }
  # decompose each element in data down to terminals
  decomposed_data = { type(value_attr).value : value_attr.value 
                        for key,value in data.items() if isinstance(key, AttributeMeta) and isinstance( value, Morph )
                          for value_attr in breadth_first(value) if value_attr.terminal }
  decomposed_data.update( (key, value) for key,value in data.items() if not isinstance(key, AttributeMeta) or not isinstance( value, Morph ) )
  # for all composite types in cls
  # mapping of type -> set of type's terminal dependencies
  # TODO : omit nested breadth_first? 
  for type_attr in breadth_first(cls):
    if type_attr.value not in _dependencies_ and not type_attr.terminal:
      _dependencies_[ type_attr.value ] = { dec_attr for dec_attr in breadth_first(type_attr.value) if dec_attr.terminal }
  
  result = None
  attempt = {}
  solve_conflicts = {None}
  
  for i in range(limit):
    # overwrite decomposed_value with decomposed_data
    attempt = dict(decomposed_value)
    attempt.update(decomposed_data)
    a0 = dict(attempt)
    # try building result
    result, solve_conflicts, shared = solve(cls, attempt, *args)
    if len(solve_conflicts) == 0:
      return result, attempt
    solve_conflicts = { conflict for pair in solve_conflicts for conflict in pair }
    # decompose shared values down to terminals
    shared_terminals = { attr for item in shared for attr in _dependencies_[item] }
    # for each composite source of conflict, add their terminal decomposition, but omit the terminals that are shared
    conflicts = { attribute for source in solve_conflicts if source.value in _dependencies_
                              for attribute in ( _dependencies_[source.value] - shared_terminals ) }
    # handle the case when the shared terminal itself is the source of conflict
    conflicts.update( shared_terminal for source in solve_conflicts if source.value in shared
                                        for shared_terminal in _dependencies_[source.value] )
    # append the terminals
    conflicts.update( solve_conflicts )
    # remove conflicts from decomposed_value
    decomposed_value = { key : value for key,value in decomposed_value.items() if key not in conflicts }
    '''print('----- attempt diff', { key : value for key,value in attempt.items() if key not in a0 or a0[key] != value})
    print('----- conflicts ',conflicts)
    print('----- solve_conflicts ',solve_conflicts)
    print('----- decomposed_value ',decomposed_value)
    print('----------------------------------')
    input()'''
  raise RuntimeError('Update iteration limit reached')
  


def construct( cls, data ):
  post_order_composites = ( attr for attr in post_order(cls) if not attr.terminal)
  for type_attr in post_order_composites:
    if type_attr not in data and all( member in data for member in type_attr.value.attr ):
      data[type_attr] = type_attr.value(data)
  return cls(data)
  
''' Builds cls instance from data dict using *args
    returns None in case of failure, uses morph to extend the amount of data
    mutates data by adding intermediate morphism results
'''
def solve( cls, data, *args ):
  # guard(data)
  conflicts = []
  created = list(data.items())
  post_order_composites = set( attr for attr in breadth_first(cls) if not attr.terminal)
  
  ''' Iteratively morphs the data and tries to construct higher-order classes
      Assures object equality through morph, but not identity in case of internal shared variables '''   
  while len(created) > 0:
    # morph the created items, push them to data
    conflicts.extend( morph( data, *args, stack=created ) )
    post_order_composites = post_order_composites - data.keys()
    # traverse cls, create members that are available        
    for type_attr in post_order_composites:
      if all( member in data for member in type_attr.value.attr ):
        created.append( (type_attr, type_attr.value(data)) )
  
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
  conflicts = []
  # d = dict(data)
  # morph the values contents
  while len(stack) > 0:
    # Get source and value from values
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
          # composites are in conflict if their terminals are in conflict, do not decompose
          results_to_process.extend( (type(attr), attr.value) for attr in breadth_first(result) if attr.terminal )
     
      stack.extend( (target,result) for target,result in results.items() if target not in data )
      data.update( results )
    else:
      pass # source does not encode transformation, so skip it
    data[source] = value
  return conflicts
  
