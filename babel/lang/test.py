import babel.lang.parser as p

with open( 'babel/lang/grammar.lang' ) as file:
  first = p.parseStr( file.read() )
  g1 = first.symtable['grammar']

Parse = g1.compile( p.compiler )

with open( 'babel/lang/grammar.lang' ) as file:
  second = p.parseStr( file.read(), Parse )
  g2 = second.symtable['grammar'] 