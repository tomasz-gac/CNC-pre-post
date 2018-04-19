import generator.rule as r
from generator.grammar import Grammar

g = Grammar()

g.coordCartesian = g.XYZABC, g.primary.push()
g.coordPolar     = g.PAPR,   g.primary.push()
g.coordCC        = g.CCXYZ,  g.primary.push()
g.pointCartesian = coordCartesian, +coordCartesian
g.pointPolar     = coordPolar, +coordPolar

g.feed       = g.F, ( [ g.MAX, g.primary ] ).push()

g.gotoTail = ~g.direction, ~g.compensation, ~g.feed

g.aux = g.auxilary & +g.auxilary

g.goto =  [ ( g.LC, (~g.pointCartesian, g.gotoTail, ~g.aux) ), 
            ( g.LPCP, ( ~g.pointPolar, ~g.coordCartesian, g.gotoTail, ~g.aux) ) ]

g.circleCenter = g.CC, g.coordCC, g.coordCC, ~g.aux

g.positioning = [ g.goto, g.circleCenter ]
g.positioningShort = (
    ( [ g.pointCartesian, g.pointPolar ], ~g.coordCartesian ), g.gotoTail, ~g.aux & g.MOVE
  ).push()

################# DO DOKONCZENIA PONIZEJ
  
  
  
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
).push()

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

