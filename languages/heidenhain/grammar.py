import generator.rule as r

coordCartesian = ('coordCartesian'  & r.make('primary').push()).push()
coordPolar     = ('coordPolar'      & r.make('primary').push()).push()
coordCC        = ('coordCC'         & r.make('primary').push()).push()

pointCartesian = coordCartesian & +coordCartesian
pointPolar     = coordPolar & +coordPolar

feed       = ( "F" & ( "MAX" | r.make('primary') ).push() ).push()
compensation = r.make('compensation').push()
direction    = r.make('direction').push()

gotoTail = ~direction & ~compensation & ~feed

goto = ( 'L/C' & ~pointCartesian | 'LP/CP' & ~pointPolar & ~coordCartesian) & gotoTail

circleCenter = 'CC' & coordCC & coordCC

auxilary = r.make('auxilary')

positioning = ( ( goto | circleCenter ) & (+auxilary).push() ).push()
positioningShort = ( 
    ( pointCartesian | pointPolar & ~coordCartesian ) & gotoTail & (+auxilary).push() & 'set'
  ).push()

comment       = r.make('comment')
begin_pgm     = 'begin_pgm'
end_pgm       = 'end_pgm'
BLKformStart  = 'block form start' & pointCartesian
BLKformEnd    = 'block form end' & pointCartesian
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
  positioningShort  |
  comment
  )
& ~comment
).push().pull()

coordCartesian.name   = 'coordCartesian'
coordPolar.name       = 'coordPolar'
coordCC.name          = 'coordCC'
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

