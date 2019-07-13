import languages.heidenhain.parser as hh
import babel as b
inp = b.State('L Z+150 FMAX')
r = hh.Parse(inp)

