def in_order( cls ):
  stack = list(cls.attr)
  while len(stack) > 0:
    member = stack.pop(-1)
    value = member.value
    yield member
    if not member.terminal:
      stack.extend( value.attr )

def post_order( cls ):
  stack = [ (member, False) for member in cls.attr ]
  while len(stack) > 0:
    member, visited = stack.pop(-1)
    value = member.value
    if not visited and not member.terminal:
      stack.append( (member, True) ) 
      stack.extend( (mem, False) for mem in value.attr )
      continue
    yield member

def breadth_first( cls ):
  stack = [ member for member in cls.attr ]
  while len(stack) > 0:
    yield from stack
    stack = [ bottom_item 
                for top_item in stack if not top_item.terminal
                  for bottom_item in top_item.value.attr ]

def make_cached( iterator ):
  _cache_ = {}
  def cached_iterator( cls ):
    try:
      yield from _cache_[cls]
    except KeyError:
      _cache_[cls] = list(iterator(cls))
      yield from _cache_[cls]
  return cached_iterator, _cache_

in_order_cached,      _in_order_cache_       = make_cached( in_order )
post_order_cached,    _post_order_cache_     = make_cached( post_order )
breadth_first_cached, _breadth_first_cache_  = make_cached( breadth_first )