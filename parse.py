# from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import sys
import babel
import languages.heidenhain.parser as hh
from babel.state import State
import math
import pickle
from os.path import basename, abspath, splitext

def parse( program, lineOffset ):
  results = []        #result list
  
  parser = hh.Parse
  symtable = {}
  for i, line in enumerate(program):
      #append the line number marker, start at 1 and use the worker thread offset
    # results.append(CNC.AST.LineNumber(i+lineOffset+1))
    try:
      state = State( line.rstrip('\n') )
      state.symtable.update( symtable )
      rest = parser( state )
      if len(rest) > 0:
        raise RuntimeError( 'Parser failed at line ' + line + ' rest: "' + rest + '"' )
      else:
        results.append( state.symtable )
        symtable.update( state.symtable )
    except RuntimeError as err:
      print(str(err))
    except babel.ParserFailedException:
      print('Parser failed at line ' + line)
  return results

  # split the lst into chunks of size sz
def split( lst, sz ):
  return [lst[i:i+sz] for i in range(0, len(lst), sz)]
    
def main():
  program = open( sys.argv[1], 'r');  
  pgmList = list(program.__iter__())
  program.close()
  
  workers = 4 # number of worker processes
    #split the program into chunks for processing
  n=math.ceil(len(pgmList)/workers)
  Chunks = split(pgmList, n)
  result = [ None for i in range(0,workers) ]
  
  print('start')
  t = time.time()
  '''with ProcessPoolExecutor(max_workers=workers) as executor:
        # Start the load operations and mark each future with its index in the result
      future_to_index = {executor.submit(parse, chunk, i*n): i for i, chunk in enumerate(Chunks)}
      for future in as_completed(future_to_index):
            #get the index of the future
          index = future_to_index[future]
          try:
                # store the result in its place in the program
              result[index] = future.result()
          except Exception as exc:
              print('Process generated an exception: %s' % (exc))
          else:
              print('Process ' + str(index) + ' finished')'''
  parseOutput = parse( pgmList, 0 )
  elapsed = time.time() - t
  print( str(elapsed) + "s elapsed" )
  
    #collapse the list of lists into a list
  # parseOutput = [ item for sublist in result for item in sublist ]
    #output to file
  
  fname = splitext(basename(sys.argv[1]))[0]+".p"
  
  '''output  = open( fname, 'wb' )
  pickle.dump( parseOutput, output )
  output.close()'''
  return parseOutput
      
  

parseOutput = main()
pgm = iter(parseOutput)