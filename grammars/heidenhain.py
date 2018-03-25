import generator.rule as r

coordinate = ('coord' & r.make('primary').push()).push()
coordinate.name = 'coordinate'
point      = coordinate & +coordinate
point.name = 'point'
feed       = ( "F" & ( "MAX" | r.make('primary') ).push() ).push()
feed.name = 'feed'
compensation = r.make('compensation')
direction    = r.make('direction')

gotoTail = ( ~direction & ~compensation & ~feed ).push()
gotoTail.name = 'gotoTail'
goto = 'L/C(P)' & ~point & gotoTail
goto.name = 'goto'
circleCenter = 'CC' & point
circleCenter.name = 'circleCenter'

auxilary = 'M' & r.make('number').push()
auxilary.name = 'auxilary'

positioning = ( ( goto | circleCenter ) & (+auxilary).push() ).push()
positioning.name = 'positioning'
positioningShort = ( point & gotoTail & (+auxilary).push() ).push()
positioningShort.name = 'positioningShort'

begin_pgm = 'begin_pgm'
end_pgm   = 'end_pgm'
comment   = r.make('comment')
BLKformStart = 'block form start' & point
BLKformStart.name = 'BLKformStart'
BLKformEnd   = 'block form end' & point
BLKformEnd.name = 'BLKformEnd'
fn_f         = 'fn_f' & r.make('expression')
fn_f.name = 'fn_f'

toolCall = ( 
  'tool call' & ( 
    r.make('primary') & ( 
      "tool axis" & 
          +( ( 'tool options' & r.make('primary').push()).push() )       
      ).push()
    ).push() 
  ).push() 
toolCall.name = 'toolCall'

heidenhain = (
 ~r.make('number') & ( 
  positioning       |
  fn_f              |
  toolCall          |
  begin_pgm         |
  end_pgm           |
  BLKformStart      |
  BLKformEnd        |
  auxilary          |
  positioningShort
  )
& ~comment
).push().pull()
heidenhain.name = 'heidenhain'