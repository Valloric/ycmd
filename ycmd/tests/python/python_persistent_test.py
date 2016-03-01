# coding: utf-8
#
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
from hamcrest import ( assert_that, contains, contains_string, empty,
                       has_entry, has_entries, has_item, has_items )
from .python_handlers_test import Python_Handlers_test
from ycmd.utils import ReadFile
import http.client
import os.path


class Python_Persistent_test( Python_Handlers_test ):

  @classmethod
  def setUpClass( cls ):
    cls._SetUpApp()
    cls()._WaitUntilJediHTTPServerReady()


  @classmethod
  def tearDownClass( cls ):
    cls()._StopJediHTTPServer()


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
                                         } ) )

    # We ignore errors here and we check the response code ourself.
    # This is to allow testing of requests returning errors.
    response = self._app.post_json( '/completions',
                                    CombineRequest( test[ 'request' ], {
                                      'contents': contents
                                    } ),
                                    expect_errors = True )

    eq_( response.status_code, test[ 'expect' ][ 'response' ] )

    assert_that( response.json, test[ 'expect' ][ 'data' ] )


  def Completion_Basic_test( self ):
    filepath = self._PathToTestFile( 'basic.py' )
    completion_data = self._BuildRequest( filepath = filepath,
                                          filetype = 'python',
                                          contents = ReadFile( filepath ),
                                          line_num = 7,
                                          column_num = 3)

    results = self._app.post_json( '/completions',
                                   completion_data ).json[ 'completions' ]

    assert_that( results,
                 has_items(
                   self._CompletionEntryMatcher( 'a' ),
                   self._CompletionEntryMatcher( 'b' ),
                   self._CompletionLocationMatcher( 'line_num', 3 ),
                   self._CompletionLocationMatcher( 'line_num', 4 ),
                   self._CompletionLocationMatcher( 'column_num', 10 ),
                   self._CompletionLocationMatcher( 'filepath', filepath ) ) )


  def Completion_UnicodeDescription_test( self ):
    filepath = self._PathToTestFile( 'unicode.py' )
    completion_data = self._BuildRequest( filepath = filepath,
                                          filetype = 'python',
                                          contents = ReadFile( filepath ),
                                          force_semantic = True,
                                          line_num = 5,
                                          column_num = 3)

    results = self._app.post_json( '/completions',
                                   completion_data ).json[ 'completions' ]
    assert_that( results, has_item(
      has_entry( 'detailed_info', contains_string( u'aafäö' ) ) ) )


  def Completion_NoSuggestions_Fallback_test( self ):
    # Python completer doesn't raise NO_COMPLETIONS_MESSAGE, so this is a
    # different code path to the Clang completer cases

    # TESTCASE2 (general_fallback/lang_python.py)
    self._RunCompletionTest( {
      'description': 'param jedi does not know about (id). query="a_p"',
      'request': {
        'filetype'  : 'python',
        'filepath'  : self._PathToTestFile( 'general_fallback',
                                            'lang_python.py' ),
        'line_num'  : 28,
        'column_num': 20,
        'force_semantic': False,
      },
      'expect': {
        'response': http.client.OK,
        'data': has_entries( {
          'completions': contains(
            self._CompletionEntryMatcher( 'a_parameter', '[ID]' ),
            self._CompletionEntryMatcher( 'another_parameter', '[ID]' ),
          ),
          'errors': empty(),
        } )
      },
    } )


  def Subcommand_GoTo_Variation_ZeroBasedLineAndColumn_test( self ):
    tests = [
      {
        'command_arguments': [ 'GoToDefinition' ],
        'response': {
          'filepath': os.path.abspath( '/foo.py' ),
          'line_num': 2,
          'column_num': 5
        }
      },
      {
        'command_arguments': [ 'GoToDeclaration' ],
        'response': {
          'filepath': os.path.abspath( '/foo.py' ),
          'line_num': 7,
          'column_num': 1
        }
      }
    ]

    for test in tests:
      yield self._Run_GoTo_Variation_ZeroBasedLineAndColumn, test


  def _Run_GoTo_Variation_ZeroBasedLineAndColumn( self, test ):
    # Example taken directly from jedi docs
    # http://jedi.jedidjah.ch/en/latest/docs/plugin-api.html#examples
    contents = """
def my_func():
  print 'called'

alias = my_func
my_list = [1, None, alias]
inception = my_list[2]

inception()
"""

    goto_data = self._BuildRequest(
        completer_target = 'filetype_default',
        command_arguments = test[ 'command_arguments' ],
        line_num = 9,
        contents = contents,
        filetype = 'python',
        filepath = '/foo.py'
    )

    eq_( test[ 'response' ],
         self._app.post_json( '/run_completer_command', goto_data ).json )


  def Subcommand_GoToDefinition_NotFound_test( self ):
    filepath = self._PathToTestFile( 'goto_file5.py' )
    goto_data = self._BuildRequest( command_arguments = [ 'GoToDefinition' ],
                                    line_num = 4,
                                    contents = ReadFile( filepath ),
                                    filetype = 'python',
                                    filepath = filepath )

    response = self._app.post_json( '/run_completer_command',
                                    goto_data,
                                    expect_errors = True  ).json
    assert_that( response,
                 self._ErrorMatcher( RuntimeError,
                                     "Can\'t jump to definition." ) )


  def Subcommand_GoTo_test( self ):
    # Tests taken from https://github.com/Valloric/YouCompleteMe/issues/1236
    tests = [
        {
          'request': { 'filename': 'goto_file1.py', 'line_num': 2 },
          'response': {
              'filepath': self._PathToTestFile( 'goto_file3.py' ),
              'line_num': 1,
              'column_num': 5
          }
        },
        {
          'request': { 'filename': 'goto_file4.py', 'line_num': 2 },
          'response': {
              'filepath': self._PathToTestFile( 'goto_file4.py' ),
              'line_num': 1,
              'column_num': 18
          }
        }
    ]
    for test in tests:
      yield self._RunSubcommandGoTo, test


  def _RunSubcommandGoTo( self, test ):
    filepath = self._PathToTestFile( test[ 'request' ][ 'filename' ] )
    goto_data = self._BuildRequest( completer_target = 'filetype_default',
                                    command_arguments = [ 'GoTo' ],
                                    line_num = test[ 'request' ][ 'line_num' ],
                                    contents = ReadFile( filepath ),
                                    filetype = 'python',
                                    filepath = filepath )

    eq_( test[ 'response' ],
         self._app.post_json( '/run_completer_command', goto_data ).json )


  def Subcommand_GetDoc_Method_test( self ):
    filepath = self._PathToTestFile( 'GetDoc.py' )
    contents = ReadFile( filepath )

    event_data = self._BuildRequest( filepath = filepath,
                                     filetype = 'python',
                                     line_num = 17,
                                     column_num = 9,
                                     contents = contents,
                                     command_arguments = [ 'GetDoc' ],
                                     completer_target = 'filetype_default' )

    response = self._app.post_json( '/run_completer_command', event_data ).json

    eq_( response, {
      'detailed_info': '_ModuleMethod()\n\n'
                       'Module method docs\n'
                       'Are dedented, like you might expect',
    } )


  def Subcommand_GetDoc_Class_test( self ):
    filepath = self._PathToTestFile( 'GetDoc.py' )
    contents = ReadFile( filepath )

    event_data = self._BuildRequest( filepath = filepath,
                                     filetype = 'python',
                                     line_num = 19,
                                     column_num = 2,
                                     contents = contents,
                                     command_arguments = [ 'GetDoc' ],
                                     completer_target = 'filetype_default' )

    response = self._app.post_json( '/run_completer_command', event_data ).json

    eq_( response, {
      'detailed_info': 'Class Documentation',
    } )


  def Subcommand_GoToReferences_test( self ):
    filepath = self._PathToTestFile( 'goto_references.py' )
    contents = ReadFile( filepath )

    event_data = self._BuildRequest( filepath = filepath,
                                     filetype = 'python',
                                     line_num = 4,
                                     column_num = 5,
                                     contents = contents,
                                     command_arguments = [ 'GoToReferences' ],
                                     completer_target = 'filetype_default' )

    response = self._app.post_json( '/run_completer_command', event_data ).json

    eq_( response, [ {
      'filepath': self._PathToTestFile( 'goto_references.py' ),
      'column_num': 5,
      'description': 'def f',
      'line_num': 1
    },
    {
      'filepath': self._PathToTestFile( 'goto_references.py' ),
      'column_num': 5,
      'description': 'a = f()',
      'line_num': 4
    },
    {
      'filepath': self._PathToTestFile( 'goto_references.py' ),
      'column_num': 5,
      'description': 'b = f()',
      'line_num': 5
    },
    {
      'filepath': self._PathToTestFile( 'goto_references.py' ),
      'column_num': 5,
      'description': 'c = f()',
      'line_num': 6
    } ] )
