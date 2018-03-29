import generator.rule as r

coordCartesian = ('coordCartesian'  & r.make('primary').push()).push()
coordPolar     = ('coordPolar'      & r.make('primary').push()).push()

pointCartesian = coordCartesian & +coordCartesian
pointPolar     = coordPolar & +coordPolar

feed       = ( "F" & ( "MAX" | r.make('primary') ).push() ).push()
compensation = r.make('compensation')
direction    = r.make('direction')

gotoTail = ( ~direction & ~compensation & ~feed ).push()

goto = ( 'L/C' & ~pointCartesian | 'LP/CP' & ~pointPolar & ~coordCartesian) & gotoTail

circleCenter = 'CC' & coordCartesian

auxilary = 'M' & r.make('number').push()

positioning = ( ( goto | circleCenter ) & (+auxilary).push() ).push()
positioningShort = ( ( pointCartesian | pointPolar & ~coordCartesian ) & gotoTail & (+auxilary).push() ).push()

comment       = r.make('comment')
begin_pgm     = 'begin_pgm'
end_pgm       = 'end_pgm'
BLKformStart  = 'block form start' & coordCartesian
BLKformEnd    = 'block form end' & coordCartesian
fn_f          = 'fn_f' & r.make('expression')

toolCall = ( 
  'tool call' & ( 
    r.make('primary') & ( 
      "tool axis" & 
          +( ( 'tool options' & r.make('primary').push()).push() )       
      ).push()
    ).push() 
  ).push() 

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

coordCartesian.name   = 'coordCartesian'
coordCartesian.name   = 'coordCartesian'
feed.name             = 'feed'
gotoTail.name         = 'gotoTail'
goto.name             = 'goto'
circleCenter.name     = 'circleCenter'
auxilary.name         = 'auxilary'
positioning.name      = 'positioning'
positioningShort.name = 'positioningShort'
BLKformStart.name     = 'BLKformStart'
BLKformEnd.name       = 'BLKformEnd'
fn_f.name             = 'fn_f'
toolCall.name         = 'toolCall'

heidenhain.name       = 'heidenhain'

