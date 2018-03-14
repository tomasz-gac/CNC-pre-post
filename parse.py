import concurrent.futures
import time
import sys
import generator as gen
import heidenhain
import CNC.AST
import math
import pickle
from os.path import basename, abspath, splitext

def parse( program, lineOffset ):
  results = []        #result list
  
  lexer  = gen.Lexer()
  parser = heidenhain.Parse
  
  for i, line in enumerate(program):
      #append the line number marker, start at 1 and use the worker thread offset
    results.append(CNC.AST.LineNumber(i+lineOffset+1))
    try:
      result, parserSuccess = parser( lexer, line.rstrip() )
      if not parserSuccess or result is gen.ParserFailed or lexer.hasInput():
        print('Parser failed at line :'+str(line))
      else:
        results += result
    except RuntimeError as err:
      print(str(line)+':'+str(err))
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
  
  module = heidenhain
  
  print('start')
  t = time.time()
  with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        # Start the load operations and mark each future with its index in the result
      future_to_index = {executor.submit(parse, chunk, i*n): i for i, chunk in enumerate(Chunks)}
      for future in concurrent.futures.as_completed(future_to_index):
            #get the index of the future
          index = future_to_index[future]
          try:
                # store the result in its place in the program
              result[index] = future.result()
          except Exception as exc:
              print('Process generated an exception: %s' % (exc))
          else:
              print('Process ' + str(index) + ' finished')
  # parseOutput = parse( pgmList, 0 )
  elapsed = time.time() - t
  print( str(elapsed) + "s elapsed" )
  
    #collapse the list of lists into a list
  parseOutput = [ item for sublist in result for item in sublist ]
    #output to file
  
  fname = splitext(basename(sys.argv[1]))[0]+".p"
  
  output  = open( fname, 'wb' )
  pickle.dump( parseOutput, output )
  output.close()
  return parseOutput
      
  

if __name__ == '__main__':
  parseOutput = main()