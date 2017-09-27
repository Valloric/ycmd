#include "ClangCompleter.h"
// iostream is included because of a bug with Python earlier than 2.7.12
// and 3.5.3 on OSX and FreeBSD.
#include <iostream>
#include <boost/python.hpp>

using YouCompleteMe::ClangCompleter;


// This small program simulates the output of the clang executable when ran with
// the -E and -v flags. It takes a list of flags and a filename as arguments and
// creates the corresponding translation unit.
// When retrieving user flags, the server executes this program as follows:
//
//   ycm_fake_clang -E -v [flag ...] filename
//
// and extract the list of system header paths from the output. These
// directories are then added to the list of flags to provide completion of
// system headers in include statements and allow jumping to these headers.
int main( int argc, char **argv ) {
  if ( argc < 2 ) {
    std::cout << "Usage: " << argv[ 0 ] << " [flag ...] filename\n";
    return EXIT_FAILURE;
  }

  Py_Initialize();
  // Necessary because of usage of the ReleaseGil class.
  PyEval_InitThreads();

  int i;
  std::vector< std::string> flags;
  for ( i = 0; i < argc - 1; i++ )
    flags.push_back( argv[ i ] );
  const char* filename = argv[ i ];

  ClangCompleter completer;
  completer.UpdateTranslationUnit( filename,
                                   std::vector< UnsavedFile >(),
                                   flags );

  return EXIT_SUCCESS;
}
