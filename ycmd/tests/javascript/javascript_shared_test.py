# Copyright (C) 2016 ycmd contributors
#
# This file is part of ycmd.
#
# ycmd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ycmd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ycmd.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from nose.tools import eq_
from hamcrest import ( assert_that, contains, contains_inanyorder, empty,
                       has_entries )
from .javascript_handlers_test import Javascript_Handlers_test
from pprint import pformat
from ycmd.utils import ReadFile
import http.client
import os


def LocationMatcher( filepath, column_num, line_num ):
  return has_entries( {
    'line_num': line_num,
    'column_num': column_num,
    'filepath': filepath
  } )


def ChunkMatcher( replacement_text, start, end ):
  return has_entries( {
    'replacement_text': replacement_text,
    'range': has_entries( {
      'start': start,
      'end': end
    } )
  } )


class Javascript_Shared_test( Javascript_Handlers_test ):

  _prev_current_dir = None

  @classmethod
  def setUpClass( cls ):
    cls._SetUpApp()
    cls._prev_current_dir = os.getcwd()
    os.chdir( cls._PathToTestFile() )

    cls()._WaitUntilTernServerReady()


  @classmethod
  def tearDownClass( cls ):
    cls()._StopTernServer()

    os.chdir( cls._prev_current_dir )


  # The following properties/methods are in Object.prototype, so are present
  # on all objects:
  #
  # toString()
  # toLocaleString()
  # valueOf()
  # hasOwnProperty()
  # propertyIsEnumerable()
  # isPrototypeOf()


  def _RunCompletionTest( self, test ):
    """
    Method to run a simple completion test and verify the result

    test is a dictionary containing:
      'request': kwargs for BuildRequest
      'expect': {
         'response': server response code (e.g. httplib.OK)
         'data': matcher for the server response json
      }
    """

    contents = ReadFile( test[ 'request' ][ 'filepath' ] )

    def CombineRequest( request, data ):
      kw = request
      request.update( data )
      return self._BuildRequest( **kw )

    self._app.post_json( '/event_notification',
                         CombineRequest( test[ 'request' ], {
                                         'event_name': 'FileReadyToParse',
                                         'contents': contents,
                                         } ),
                         expect_errors = True )

    # We ignore errors here and we check the response code ourself.
    # This is to allow testing of requests returning errors.
    response = self._app.post_json( '/completions',
                                    CombineRequest( test[ 'request' ], {
                                      'contents': contents
                                    } ),
                                    expect_errors = True )

    print( 'completer response: {0}'.format( pformat( response.json ) ) )

    eq_( response.status_code, test[ 'expect' ][ 'response' ] )

    assert_that( response.json, test[ 'expect' ][ 'data' ] )


  def Completion_NoQuery_test( self ):
    self._RunCompletionTest( {
      'description': 'semantic completion works for simple object no query',
      'request': {
        'filetype'  : 'javascript',
        'filepath'  : self._PathToTestFile( 'simple_test.js' ),
        'line_num'  : 13,
        'column_num': 43,
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'completions': contains_inanyorder(
            self._CompletionEntryMatcher( 'a_simple_function',
                                          'fn(param: ?) -> string' ),
            self._CompletionEntryMatcher( 'basic_type', 'number' ),
            self._CompletionEntryMatcher( 'object', 'object' ),
            self._CompletionEntryMatcher( 'toString', 'fn() -> string' ),
            self._CompletionEntryMatcher( 'toLocaleString', 'fn() -> string' ),
            self._CompletionEntryMatcher( 'valueOf', 'fn() -> number' ),
            self._CompletionEntryMatcher( 'hasOwnProperty',
                                          'fn(prop: string) -> bool' ),
            self._CompletionEntryMatcher( 'isPrototypeOf',
                                          'fn(obj: ?) -> bool' ),
            self._CompletionEntryMatcher( 'propertyIsEnumerable',
                                          'fn(prop: string) -> bool' ),
          ),
          'errors': empty(),
        } )
      },
    } )


  def Completion_Query_test( self ):
    self._RunCompletionTest( {
      'description': 'semantic completion works for simple object with query',
      'request': {
        'filetype'  : 'javascript',
        'filepath'  : self._PathToTestFile( 'simple_test.js' ),
        'line_num'  : 14,
        'column_num': 45,
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'completions': contains(
            self._CompletionEntryMatcher( 'basic_type', 'number' ),
            self._CompletionEntryMatcher( 'isPrototypeOf',
                                          'fn(obj: ?) -> bool' ),
          ),
          'errors': empty(),
        } )
      },
    } )


  def Completion_Require_NoQuery_test( self ):
    self._RunCompletionTest( {
      'description': 'semantic completion works for simple object no query',
      'request': {
        'filetype'  : 'javascript',
        'filepath'  : self._PathToTestFile( 'requirejs_test.js' ),
        'line_num'  : 2,
        'column_num': 15,
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'completions': contains_inanyorder(
            self._CompletionEntryMatcher( 'mine_bitcoin',
                                          'fn(how_much: ?) -> number' ),
            self._CompletionEntryMatcher( 'get_number', 'number' ),
            self._CompletionEntryMatcher( 'get_string', 'string' ),
            self._CompletionEntryMatcher( 'get_thing',
                                          'fn(a: ?) -> number|string' ),
            self._CompletionEntryMatcher( 'toString', 'fn() -> string' ),
            self._CompletionEntryMatcher( 'toLocaleString', 'fn() -> string' ),
            self._CompletionEntryMatcher( 'valueOf', 'fn() -> number' ),
            self._CompletionEntryMatcher( 'hasOwnProperty',
                                          'fn(prop: string) -> bool' ),
            self._CompletionEntryMatcher( 'isPrototypeOf',
                                          'fn(obj: ?) -> bool' ),
            self._CompletionEntryMatcher( 'propertyIsEnumerable',
                                          'fn(prop: string) -> bool' ),
          ),
          'errors': empty(),
        } )
      },
    } )


  def Completion_Require_Query_test( self ):
    self._RunCompletionTest( {
      'description': 'semantic completion works for require object with query',
      'request': {
        'filetype'  : 'javascript',
        'filepath'  : self._PathToTestFile( 'requirejs_test.js' ),
        'line_num'  : 3,
        'column_num': 17,
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'completions': contains(
            self._CompletionEntryMatcher( 'mine_bitcoin',
                                          'fn(how_much: ?) -> number' ),
          ),
          'errors': empty(),
        } )
      },
    } )


  def Completion_Require_Query_LCS_test( self ):
    self._RunCompletionTest( {
      'description': ( 'completion works for require object '
                       'with query not prefix' ),
      'request': {
        'filetype'  : 'javascript',
        'filepath'  : self._PathToTestFile( 'requirejs_test.js' ),
        'line_num'  : 4,
        'column_num': 17,
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'completions': contains(
            self._CompletionEntryMatcher( 'get_number', 'number' ),
            self._CompletionEntryMatcher( 'get_thing',
                                          'fn(a: ?) -> number|string' ),
            self._CompletionEntryMatcher( 'get_string', 'string' ),
          ),
          'errors': empty(),
        } )
      },
    } )


  def Completion_DirtyNamedBuffers_test( self ):
    # This tests that when we have dirty buffers in our editor, tern actually
    # uses them correctly
    self._RunCompletionTest( {
      'description': ( 'completion works for require object '
                       'with query not prefix' ),
      'request': {
        'filetype'  : 'javascript',
        'filepath'  : self._PathToTestFile( 'requirejs_test.js' ),
        'line_num'  : 18,
        'column_num': 11,
        'file_data': {
          self._PathToTestFile( 'no_such_lib', 'no_such_file.js' ): {
            'contents': (
              'define( [], function() { return { big_endian_node: 1 } } )' ),
            'filetypes': [ 'javascript' ]
          }
        },
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'completions': contains_inanyorder(
            self._CompletionEntryMatcher( 'big_endian_node', 'number' ),
            self._CompletionEntryMatcher( 'toString', 'fn() -> string' ),
            self._CompletionEntryMatcher( 'toLocaleString', 'fn() -> string' ),
            self._CompletionEntryMatcher( 'valueOf', 'fn() -> number' ),
            self._CompletionEntryMatcher( 'hasOwnProperty',
                                          'fn(prop: string) -> bool' ),
            self._CompletionEntryMatcher( 'isPrototypeOf',
                                          'fn(obj: ?) -> bool' ),
            self._CompletionEntryMatcher( 'propertyIsEnumerable',
                                          'fn(prop: string) -> bool' ),
          ),
          'errors': empty(),
        } )
      },
    } )


  def Completion_ReturnsDocsInCompletions_test( self ):
    # This tests that we supply docs for completions
    self._RunCompletionTest( {
      'description': 'completions supply docs',
      'request': {
        'filetype'  : 'javascript',
        'filepath'  : self._PathToTestFile( 'requirejs_test.js' ),
        'line_num'  : 8,
        'column_num': 15,
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'completions': contains_inanyorder(
            self._CompletionEntryMatcher(
              'a_function',
              'fn(bar: ?) -> {a_value: string}', {
                'detailed_info': ( 'fn(bar: ?) -> {a_value: string}\n'
                                   'This is a short documentation string'),
              } ),
            self._CompletionEntryMatcher( 'options', 'options' ),
            self._CompletionEntryMatcher( 'toString', 'fn() -> string' ),
            self._CompletionEntryMatcher( 'toLocaleString', 'fn() -> string' ),
            self._CompletionEntryMatcher( 'valueOf', 'fn() -> number' ),
            self._CompletionEntryMatcher( 'hasOwnProperty',
                                          'fn(prop: string) -> bool' ),
            self._CompletionEntryMatcher( 'isPrototypeOf',
                                          'fn(obj: ?) -> bool' ),
            self._CompletionEntryMatcher( 'propertyIsEnumerable',
                                          'fn(prop: string) -> bool' ),
          ),
          'errors': empty(),
        } )
      },
    } )


  def _RunSubcommandTest( self, test ):
    contents = ReadFile( test[ 'request' ][ 'filepath' ] )

    def CombineRequest( request, data ):
      kw = request
      request.update( data )
      return self._BuildRequest( **kw )

    # Because we aren't testing this command, we *always* ignore errors. This
    # is mainly because we (may) want to test scenarios where the completer
    # throws an exception and the easiest way to do that is to throw from
    # within the FlagsForFile function.
    self._app.post_json( '/event_notification',
                         CombineRequest( test[ 'request' ], {
                                         'event_name': 'FileReadyToParse',
                                         'contents': contents,
                                         } ),
                         expect_errors = True )

    # We also ignore errors here, but then we check the response code
    # ourself. This is to allow testing of requests returning errors.
    response = self._app.post_json(
      '/run_completer_command',
      CombineRequest( test[ 'request' ], {
        'completer_target': 'filetype_default',
        'contents': contents,
        'filetype': 'javascript',
        'command_arguments': ( [ test[ 'request' ][ 'command' ] ]
                               + test[ 'request' ].get( 'arguments', [] ) )
      } ),
      expect_errors = True
    )

    print( 'completer response: {0}'.format( pformat( response.json ) ) )

    eq_( response.status_code, test[ 'expect' ][ 'response' ] )

    assert_that( response.json, test[ 'expect' ][ 'data' ] )


  def Subcommand_DefinedSubcommands_test( self ):
    subcommands_data = self._BuildRequest( completer_target = 'javascript' )

    eq_( sorted( [ 'GoToDefinition',
                   'GoTo',
                   'GetDoc',
                   'GetType',
                   'StartServer',
                   'StopServer',
                   'GoToReferences',
                   'RefactorRename' ] ),
         self._app.post_json( '/defined_subcommands',
                              subcommands_data ).json )


  def Subcommand_GoToDefinition_test( self ):
    self._RunSubcommandTest( {
      'description': 'GoToDefinition works within file',
      'request': {
        'command': 'GoToDefinition',
        'line_num': 13,
        'column_num': 25,
        'filepath': self._PathToTestFile( 'simple_test.js' ),
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'filepath': self._PathToTestFile( 'simple_test.js' ),
          'line_num': 1,
          'column_num': 5,
        } )
      }
    } )


  def Subcommand_GoTo_test( self ):
    self._RunSubcommandTest( {
      'description': 'GoTo works the same as GoToDefinition within file',
      'request': {
        'command': 'GoTo',
        'line_num': 13,
        'column_num': 25,
        'filepath': self._PathToTestFile( 'simple_test.js' ),
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'filepath': self._PathToTestFile( 'simple_test.js' ),
          'line_num': 1,
          'column_num': 5,
        } )
      }
    } )


  def Subcommand_GetDoc_test( self ):
    self._RunSubcommandTest( {
      'description': 'GetDoc works within file',
      'request': {
        'command': 'GetDoc',
        'line_num': 7,
        'column_num': 16,
        'filepath': self._PathToTestFile( 'coollib', 'cool_object.js' ),
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'detailed_info': (
            'Name: mine_bitcoin\n'
            'Type: fn(how_much: ?) -> number\n\n'
            'This function takes a number and invests it in bitcoin. It '
            'returns\nthe expected value (in notional currency) after 1 year.'
          )
        } )
      }
    } )


  def Subcommand_GetType_test( self ):
    self._RunSubcommandTest( {
      'description': 'GetType works within file',
      'request': {
        'command': 'GetType',
        'line_num': 11,
        'column_num': 14,
        'filepath': self._PathToTestFile( 'coollib', 'cool_object.js' ),
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'message': 'number'
        } )
      }
    } )


  def Subcommand_GoToReferences_test( self ):
    self._RunSubcommandTest( {
      'description': 'GoToReferences works within file',
      'request': {
        'command': 'GoToReferences',
        'line_num': 17,
        'column_num': 29,
        'filepath': self._PathToTestFile( 'coollib', 'cool_object.js' ),
      },
      'expect': {
        'response': http.client.OK,
        'data': contains_inanyorder(
          has_entries( {
            'filepath': self._PathToTestFile( 'coollib', 'cool_object.js' ),
            'line_num':  17,
            'column_num': 29,
          } ),
          has_entries( {
            'filepath': self._PathToTestFile( 'coollib', 'cool_object.js' ),
            'line_num': 12,
            'column_num': 9,
          } )
        )
      }
    } )


  def Subcommand_GetDocWithNoItendifier_test( self ):
    self._RunSubcommandTest( {
      'description': 'GetDoc works when no identifier',
      'request': {
        'command': 'GetDoc',
        'filepath': self._PathToTestFile( 'simple_test.js' ),
        'line_num': 12,
        'column_num': 1,
      },
      'expect': {
        'response': http.client.INTERNAL_SERVER_ERROR,
        'data': self._ErrorMatcher( RuntimeError, 'TernError: No type found '
                                                  'at the given position.' ),
      }
    } )


  def Subcommand_RefactorRename_Simple_test( self ):
    filepath = self._PathToTestFile( 'simple_test.js' )
    self._RunSubcommandTest( {
      'description': 'RefactorRename works within a single scope/file',
      'request': {
        'command': 'RefactorRename',
        'arguments': [ 'test' ],
        'filepath': filepath,
        'line_num': 15,
        'column_num': 32,
      },
      'expect': {
        'response': http.client.OK,
        'data': {
          'fixits': contains( has_entries( {
            'chunks': contains(
                ChunkMatcher( 'test',
                              LocationMatcher( filepath, 1, 5 ),
                              LocationMatcher( filepath, 1, 22 ) ),
                ChunkMatcher( 'test',
                              LocationMatcher( filepath, 13, 25 ),
                              LocationMatcher( filepath, 13, 42 ) ),
                ChunkMatcher( 'test',
                              LocationMatcher( filepath, 14, 24 ),
                              LocationMatcher( filepath, 14, 41 ) ),
                ChunkMatcher( 'test',
                              LocationMatcher( filepath, 15, 24 ),
                              LocationMatcher( filepath, 15, 41 ) ),
                ChunkMatcher( 'test',
                              LocationMatcher( filepath, 21, 7 ),
                              LocationMatcher( filepath, 21, 24 ) ),
                # On the same line, ensuring offsets are as expected (as
                # unmodified source, similar to clang)
                ChunkMatcher( 'test',
                              LocationMatcher( filepath, 21, 28 ),
                              LocationMatcher( filepath, 21, 45 ) ),
            ) ,
            'location': LocationMatcher( filepath, 15, 32 )
          } ) )
        }
      }
    } )


  def Subcommand_RefactorRename_MultipleFiles_test( self ):
    file1 = self._PathToTestFile( 'file1.js' )
    file2 = self._PathToTestFile( 'file2.js' )
    file3 = self._PathToTestFile( 'file3.js' )

    self._RunSubcommandTest( {
      'description': 'RefactorRename works across files',
      'request': {
        'command': 'RefactorRename',
        'arguments': [ 'a-quite-long-string' ],
        'filepath': file1,
        'line_num': 3,
        'column_num': 14,
      },
      'expect': {
        'response': http.client.OK,
        'data': {
          'fixits': contains( has_entries( {
            'chunks': contains(
              ChunkMatcher(
                'a-quite-long-string',
                LocationMatcher( file1, 1, 5 ),
                LocationMatcher( file1, 1, 11 ) ),
              ChunkMatcher(
                'a-quite-long-string',
                LocationMatcher( file1, 3, 14 ),
                LocationMatcher( file1, 3, 19 ) ),
              ChunkMatcher(
                'a-quite-long-string',
                LocationMatcher( file2, 2, 14 ),
                LocationMatcher( file2, 2, 19 ) ),
              ChunkMatcher(
                'a-quite-long-string',
                LocationMatcher( file3, 3, 12 ),
                LocationMatcher( file3, 3, 17 ) )
            ) ,
            'location': LocationMatcher( file1, 3, 14 )
          } ) )
        }
      }
    } )


  def Subcommand_RefactorRename_MultipleFiles_OnFileReadyToParse_test( self ):
    file1 = self._PathToTestFile( 'file1.js' )
    file2 = self._PathToTestFile( 'file2.js' )
    file3 = self._PathToTestFile( 'file3.js' )

    # This test is roughly the same as the previous one, except here file4.js is
    # pushed into the Tern engine via 'opening it in the editor' (i.e.
    # FileReadyToParse event). The first 3 are loaded into the tern server
    # because they are listed in the .tern-project file's loadEagerly option.
    file4 = self._PathToTestFile( 'file4.js' )

    self._app.post_json( '/event_notification',
                         self._BuildRequest( **{
                           'filetype': 'javascript',
                           'event_name': 'FileReadyToParse',
                           'contents': ReadFile( file4 ),
                           'filepath': file4,
                         } ),
                         expect_errors = False )

    self._RunSubcommandTest( {
      'description': 'FileReadyToParse loads files into tern server',
      'request': {
        'command': 'RefactorRename',
        'arguments': [ 'a-quite-long-string' ],
        'filepath': file1,
        'line_num': 3,
        'column_num': 14,
      },
      'expect': {
        'response': http.client.OK,
        'data': {
          'fixits': contains( has_entries( {
            'chunks': contains(
              ChunkMatcher(
                'a-quite-long-string',
                LocationMatcher( file1, 1, 5 ),
                LocationMatcher( file1, 1, 11 ) ),
              ChunkMatcher(
                'a-quite-long-string',
                LocationMatcher( file1, 3, 14 ),
                LocationMatcher( file1, 3, 19 ) ),
              ChunkMatcher(
                'a-quite-long-string',
                LocationMatcher( file2, 2, 14 ),
                LocationMatcher( file2, 2, 19 ) ),
              ChunkMatcher(
                'a-quite-long-string',
                LocationMatcher( file3, 3, 12 ),
                LocationMatcher( file3, 3, 17 ) ),
              ChunkMatcher(
                'a-quite-long-string',
                LocationMatcher( file4, 4, 22 ),
                LocationMatcher( file4, 4, 28 ) )
            ) ,
            'location': LocationMatcher( file1, 3, 14 )
          } ) )
        }
      }
    } )


  def Subcommand_RefactorRename_Missing_New_Name_test( self ):
    self._RunSubcommandTest( {
      'description': 'FixItRename raises an error without new name',
      'request': {
        'command': 'FixItRename',
        'line_num': 17,
        'column_num': 29,
        'filepath': self._PathToTestFile( 'coollib', 'cool_object.js' ),
      },
      'expect': {
        'response': http.client.INTERNAL_SERVER_ERROR,
        'data': {
          'exception': self._ErrorMatcher(
                                  ValueError,
                                  'Please specify a new name to rename it to.\n'
                                  'Usage: RefactorRename <new name>' ),
        },
      }
    } )
