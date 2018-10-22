import generator.lang.parser as p

with open( 'generator/lang/grammar.lang' ) as file:
  first = p.parseStr( file.read() )
  g1 = first.symtable['grammar']

Parse = g1.compile( p.compiler )

with open( 'generator/lang/grammar.lang' ) as file:
  second = p.parseStr( file.read(), Parse )
  g2 = second.symtable['grammar'] 