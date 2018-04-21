import generator.rule as r
from generator.grammar import Grammar

g = Grammar()

g.coordCartesian = g.XYZABC, g.primary.push()
g.coordPolar     = g.PAPR,   g.primary.push()
g.coordCC        = g.CCXYZ,  g.primary.push()
g.pointCartesian = g.coordCartesian, +g.coordCartesian
g.pointPolar     = g.coordPolar, +g.coordPolar

g.feed = g.F, r.alt( g.MAX, g.primary ).push()

g.gotoTail = ~g.direction, ~g.compensation, ~g.feed

g.aux = g.auxilary & +g.auxilary

g.goto =  r.alt(
            ( g.LC, (~g.pointCartesian, g.gotoTail, ~g.aux) ), 
            ( g.LPCP, ( ~g.pointPolar, ~g.coordCartesian, g.gotoTail, ~g.aux) ) 
          )

g.circleCenter = g.CC, g.coordCC, g.coordCC, ~g.aux

g.positioning = r.alt( g.goto, g.circleCenter )
g.positioningShort = r.seq(
    ( [ g.pointCartesian, g.pointPolar ], ~g.coordCartesian ), g.gotoTail, ~g.aux, g.MOVE
  ).push()
  
  
g.BLKformStart  = 'blockFormStart' & g.pointCartesian
g.BLKformEnd    = 'blockFormEnd' & g.pointCartesian
g.fn_f          = 'fn_f' & g.expression.push()

toolCall = 'tool call', (g.primary, ('tool axis', +r.seq( 'tool options', g.primary.push())))

g.heidenhain = r.seq(
 ~g.lineno.push(), r.alt(
  g.positioning,
  g.fn_f,
  g.toolCall,
  g.begin_pgm,
  g.end_pgm,
  g.BLKformStart,
  g.BLKformEnd,
  (g.aux, g.UPDATE),
  g.positioningShort,
  g.comment
  )
, ~g.comment
).push()