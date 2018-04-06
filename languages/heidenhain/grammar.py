import generator.rule as r

coordCartesian = 'XYZABC'  & r.make('primary').push()
coordPolar     = 'PAPR'    & r.make('primary').push()
coordCC        = 'CCXYZ'   & r.make('primary').push()
pointCartesian = coordCartesian & +coordCartesian
pointPolar     = coordPolar & +coordPolar

feed       = "F" & ( "MAX" | r.make('primary') ).push()
compensation = r.make('compensation').push()
direction    = r.make('direction').push()

gotoTail = ~direction & ~compensation & ~feed

goto = (  'L/C' & (~pointCartesian & gotoTail ) | 
          'LP/CP' & ( ~pointPolar & ~coordCartesian & gotoTail ) )

circleCenter = 'CC' & coordCC & coordCC

auxilary = 'auxilary' & +r.make('auxilary')

positioning = ( goto | circleCenter ) & ~auxilary
positioningShort = (
    ( pointCartesian | pointPolar & ~coordCartesian ) & gotoTail & ~auxilary & 'MOVE'
  ).push()

comment       = r.make('comment')
begin_pgm     = 'begin_pgm'
end_pgm       = 'end_pgm'
BLKformStart  = 'block form start' & pointCartesian
BLKformEnd    = 'block form end' & pointCartesian
fn_f          = 'fn_f' & r.make('expression').push()

toolCall = 'tool call' & ( r.make('primary') & ( 
  "tool axis" & +( ( 'tool options' & r.make('primary').push() ) ) ) )
      

heidenhain = (
 ~r.make('lineno').push() & ( 
  positioning         |
  fn_f                |
  toolCall            |
  begin_pgm           |
  end_pgm             |
  BLKformStart        |
  BLKformEnd          |
  auxilary & 'UPDATE' |
  positioningShort    |
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

