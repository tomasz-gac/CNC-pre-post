import generator as gen
import generator.rule as r

coordinate = ('coord' & r.make('primary')['sink'])['sink']
point      = coordinate & +coordinate
feed       = ( "F" & ( "MAX" | r.make('primary') )['sink'] )['sink']
compensation = r.make('compensation')
direction    = r.make('direction')

gotoTail = ( ~direction & ~compensation & ~feed )['sink']
goto = 'L/C(P)' & ~point & gotoTail
circleCenter = 'CC' & point

auxilary = 'M' & r.make('number')['sink']

positioning = ( ( goto | circleCenter ) & (+auxilary)['sink'] )['sink']
positioningShort = ( point & gotoTail & (+auxilary)['sink'] )['sink']

begin_pgm = 'begin_pgm'
end_pgm   = 'end_pgm'
comment   = r.make('comment')
BLKformStart = 'block form start' & point
BLKformEnd   = 'block form end' & point
fn_f         = 'fn_f' & r.make('expression')

toolCall = ( 
  'tool call' & ( 
    r.make('primary') & ( 
      "tool axis" & 
          +( ( 'tool options' & r.make('primary')['sink'])['sink'] )       
      )['sink']
    )['sink'] 
  )['sink'] 
  

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
)['sink']['source']
