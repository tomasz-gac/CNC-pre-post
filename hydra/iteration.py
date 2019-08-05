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

def terminals( cls ):
  stack = [ member for member in cls.attr ]
  while len(stack) > 0:
    yield from stack
    stack = [ bottom_item 
                for top_item in stack if not top_item.terminal
                  for bottom_item in top_item.value.attr ]
