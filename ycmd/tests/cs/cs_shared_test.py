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

from webtest import AppError
from .cs_handlers_test import Cs_Handlers_test
from contextlib import contextmanager
from nose.tools import eq_
from hamcrest import ( assert_that, contains, contains_string, empty, equal_to,
                       greater_than, has_entry, has_entries, has_item,
                       has_items )
from ycmd.utils import ReadFile


class Cs_Shared_test( Cs_Handlers_test ):

  _filepaths = []

  @classmethod
  def setUpClass( cls ):
    cls._SetUpApp()
    cls._app.post_json(
      '/ignore_extra_conf_file',
      { 'filepath': cls._PathToTestFile( '.ycm_extra_conf.py' ) } )


  @classmethod
  def tearDownClass( cls ):
    for filepath in cls._filepaths:
      cls()._StopOmniSharpServer( filepath )


  @contextmanager
  def _WrapOmniSharpServer( self, filepath ):
    if filepath not in self._filepaths:
      self._StartOmniSharpServer( filepath )
      self._filepaths.append( filepath )
    self._WaitUntilOmniSharpServerReady( filepath )
    yield


  def Completion_Basic_test( self ):
    filepath = self._PathToTestFile( 'testy', 'Program.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      completion_data = self._BuildRequest( filepath = filepath,
                                            filetype = 'cs',
                                            contents = contents,
                                            line_num = 10,
                                            column_num = 12 )
      response_data = self._app.post_json( '/completions',
                                           completion_data ).json
      assert_that( response_data[ 'completions' ],
                   has_items( self._CompletionEntryMatcher( 'CursorLeft' ),
                              self._CompletionEntryMatcher( 'CursorSize' ) ) )
      eq_( 12, response_data[ 'completion_start_column' ] )


  def Completion_MultipleSolution_test( self ):
    filepaths = [ self._PathToTestFile( 'testy', 'Program.cs' ),
                  self._PathToTestFile( 'testy-multiple-solutions',
                                        'solution-named-like-folder',
                                        'testy',
                                        'Program.cs' ) ]
    lines = [ 10, 9 ]
    for filepath, line in zip( filepaths, lines ):
      with self._WrapOmniSharpServer( filepath ):
        contents = ReadFile( filepath )

        completion_data = self._BuildRequest( filepath = filepath,
                                              filetype = 'cs',
                                              contents = contents,
                                              line_num = line,
                                              column_num = 12 )
        response_data = self._app.post_json( '/completions',
                                             completion_data ).json
        assert_that(
          response_data[ 'completions' ],
          has_items( self._CompletionEntryMatcher( 'CursorLeft' ),
                     self._CompletionEntryMatcher( 'CursorSize' ) )
        )
        eq_( 12, response_data[ 'completion_start_column' ] )


  def Completion_PathWithSpace_test( self ):
    filepath = self._PathToTestFile( u'неприличное слово', 'Program.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      completion_data = self._BuildRequest( filepath = filepath,
                                            filetype = 'cs',
                                            contents = contents,
                                            line_num = 9,
                                            column_num = 12 )
      response_data = self._app.post_json( '/completions',
                                           completion_data ).json
      assert_that( response_data[ 'completions' ],
                   has_items( self._CompletionEntryMatcher( 'CursorLeft' ),
                              self._CompletionEntryMatcher( 'CursorSize' ) ) )
      eq_( 12, response_data[ 'completion_start_column' ] )


  def Completion_HasBothImportsAndNonImport_test( self ):
    filepath = self._PathToTestFile( 'testy', 'ImportTest.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      completion_data = self._BuildRequest( filepath = filepath,
                                            filetype = 'cs',
                                            contents = contents,
                                            line_num = 9,
                                            column_num = 12,
                                            force_semantic = True,
                                            query = 'Date' )
      response_data = self._app.post_json( '/completions',
                                           completion_data ).json

      assert_that(
        response_data[ 'completions' ],
        has_items( self._CompletionEntryMatcher( 'DateTime' ),
                   self._CompletionEntryMatcher( 'DateTimeStyles' ) )
      )


  def Completion_ImportsOrderedAfter_test( self ):
    filepath = self._PathToTestFile( 'testy', 'ImportTest.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      completion_data = self._BuildRequest( filepath = filepath,
                                            filetype = 'cs',
                                            contents = contents,
                                            line_num = 9,
                                            column_num = 12,
                                            force_semantic = True,
                                            query = 'Date' )
      response_data = self._app.post_json( '/completions',
                                           completion_data ).json

      min_import_index = min(
        loc for loc, val
        in enumerate( response_data[ 'completions' ] )
        if val[ 'extra_data' ][ 'required_namespace_import' ]
      )

      max_nonimport_index = max(
        loc for loc, val
        in enumerate( response_data[ 'completions' ] )
        if not val[ 'extra_data' ][ 'required_namespace_import' ]
      )

      assert_that( min_import_index, greater_than( max_nonimport_index ) ),


  def ForcedReturnsResults_test( self ):
    filepath = self._PathToTestFile( 'testy', 'ContinuousTest.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      completion_data = self._BuildRequest( filepath = filepath,
                                            filetype = 'cs',
                                            contents = contents,
                                            line_num = 9,
                                            column_num = 21,
                                            force_semantic = True,
                                            query = 'Date' )
      response_data = self._app.post_json( '/completions',
                                           completion_data ).json

      assert_that(
        response_data[ 'completions' ],
        has_items( self._CompletionEntryMatcher( 'String' ),
                   self._CompletionEntryMatcher( 'StringBuilder' ) )
      )


  def Completion_NonForcedReturnsNoResults_test( self ):
    filepath = self._PathToTestFile( 'testy', 'ContinuousTest.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )
      event_data = self._BuildRequest( filepath = filepath,
                                       filetype = 'cs',
                                       contents = contents,
                                       event_name = 'FileReadyToParse' )

      self._app.post_json( '/event_notification', event_data )

      completion_data = self._BuildRequest( filepath = filepath,
                                            filetype = 'cs',
                                            contents = contents,
                                            line_num = 9,
                                            column_num = 21,
                                            force_semantic = False,
                                            query = 'Date' )
      results = self._app.post_json( '/completions', completion_data ).json

      # There are no semantic completions. However, we fall back to identifier
      # completer in this case.
      assert_that( results, has_entries( {
        'completions': has_item( has_entries( {
          'insertion_text' : 'String',
          'extra_menu_info': '[ID]',
        } ) ),
        'errors': empty(),
      } ) )


  def Completion_ForcedDividesCache_test( self ):
    filepath = self._PathToTestFile( 'testy', 'ContinuousTest.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )
      event_data = self._BuildRequest( filepath = filepath,
                                       filetype = 'cs',
                                       contents = contents,
                                       event_name = 'FileReadyToParse' )

      self._app.post_json( '/event_notification', event_data )

      completion_data = self._BuildRequest( filepath = filepath,
                                            filetype = 'cs',
                                            contents = contents,
                                            line_num = 9,
                                            column_num = 21,
                                            force_semantic = True,
                                            query = 'Date' )
      results = self._app.post_json( '/completions', completion_data ).json

      assert_that( results[ 'completions' ], not( empty() ) )
      assert_that( results[ 'errors' ], empty() )

      completion_data = self._BuildRequest( filepath = filepath,
                                            filetype = 'cs',
                                            contents = contents,
                                            line_num = 9,
                                            column_num = 21,
                                            force_semantic = False,
                                            query = 'Date' )
      results = self._app.post_json( '/completions', completion_data ).json

      # There are no semantic completions. However, we fall back to identifier
      # completer in this case.
      assert_that( results, has_entries( {
        'completions': has_item( has_entries( {
          'insertion_text' : 'String',
          'extra_menu_info': '[ID]',
        } ) ),
        'errors': empty(),
      } ) )


  def Completion_ReloadSolution_Basic_test( self ):
    filepath = self._PathToTestFile( 'testy', 'Program.cs' )
    with self._WrapOmniSharpServer( filepath ):
      result = self._app.post_json(
        '/run_completer_command',
        self._BuildRequest( completer_target = 'filetype_default',
                            command_arguments = [ 'ReloadSolution' ],
                            filepath = filepath,
                            filetype = 'cs' ) ).json

      eq_( result, True )


  def Completion_ReloadSolution_MultipleSolution_test( self ):
    filepaths = [ self._PathToTestFile( 'testy', 'Program.cs' ),
                  self._PathToTestFile( 'testy-multiple-solutions',
                                        'solution-named-like-folder',
                                        'testy',
                                        'Program.cs' ) ]
    for filepath in filepaths:
      with self._WrapOmniSharpServer( filepath ):
        result = self._app.post_json(
          '/run_completer_command',
          self._BuildRequest( completer_target = 'filetype_default',
                              command_arguments = [ 'ReloadSolution' ],
                              filepath = filepath,
                              filetype = 'cs' ) ).json

        eq_( result, True )


  def _SolutionSelectCheck( self, sourcefile, reference_solution,
                            extra_conf_store = None ):
    # reusable test: verify that the correct solution (reference_solution) is
    #   detected for a given source file (and optionally a given extra_conf)
    if extra_conf_store:
      self._app.post_json( '/load_extra_conf_file',
                           { 'filepath': extra_conf_store } )

    result = self._app.post_json(
      '/run_completer_command',
      self._BuildRequest( completer_target = 'filetype_default',
                          command_arguments = [ 'SolutionFile' ],
                          filepath = sourcefile,
                          filetype = 'cs' ) ).json

    # Now that cleanup is done, verify solution file
    eq_( reference_solution, result )


  def Completion_UsesSubfolderHint_test( self ):
    self._SolutionSelectCheck(
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-named-like-folder',
                            'testy', 'Program.cs' ),
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-named-like-folder',
                            'testy.sln' ) )


  def Completion_UsesSuperfolderHint_test( self ):
    self._SolutionSelectCheck(
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-named-like-folder',
                            'not-testy', 'Program.cs' ),
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-named-like-folder',
                            'solution-named-like-folder.sln' ) )


  def Completion_ExtraConfStoreAbsolute_test( self ):
    self._SolutionSelectCheck(
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-not-named-like-folder', 'extra-conf-abs',
                            'testy', 'Program.cs' ),
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-not-named-like-folder', 'testy2.sln' ),
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-not-named-like-folder', 'extra-conf-abs',
                            '.ycm_extra_conf.py' ) )


  def Completion_ExtraConfStoreRelative_test( self ):
    self._SolutionSelectCheck(
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-not-named-like-folder', 'extra-conf-rel',
                            'testy', 'Program.cs' ),
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-not-named-like-folder', 'extra-conf-rel',
                            'testy2.sln' ),
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-not-named-like-folder', 'extra-conf-rel',
                            '.ycm_extra_conf.py' ) )


  def Completion_ExtraConfStoreNonexisting_test( self ):
    self._SolutionSelectCheck(
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-not-named-like-folder', 'extra-conf-bad',
                            'testy', 'Program.cs' ),
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-not-named-like-folder', 'extra-conf-bad',
                            'testy2.sln' ),
      self._PathToTestFile( 'testy-multiple-solutions',
                            'solution-not-named-like-folder', 'extra-conf-bad',
                            'testy', '.ycm_extra_conf.py' ) )


  def Completion_DoesntStartWithAmbiguousMultipleSolutions_test( self ):
    filepath = self._PathToTestFile( 'testy-multiple-solutions',
                                     'solution-not-named-like-folder',
                                     'testy', 'Program.cs' )
    contents = ReadFile( filepath )
    event_data = self._BuildRequest( filepath = filepath,
                                     filetype = 'cs',
                                     contents = contents,
                                     event_name = 'FileReadyToParse' )

    exception_caught = False
    try:
      self._app.post_json( '/event_notification', event_data )
    except AppError as e:
      if 'Autodetection of solution file failed' in str( e ):
        exception_caught = True

    # The test passes if we caught an exception when trying to start it,
    # so raise one if it managed to start
    if not exception_caught:
      self._WaitUntilOmniSharpServerReady( filepath )
      self._StopOmniSharpServer( filepath )
      raise Exception( 'The Omnisharp server started, despite us not being '
                       'able to find a suitable solution file to feed it. Did '
                       'you fiddle with the solution finding code in '
                       'cs_completer.py? Hopefully you\'ve enhanced it: you '
                       'need to update this test then :)' )


  def Diagnostic_ZeroBasedLineAndColumn_test( self ):
    filepath = self._PathToTestFile( 'testy', 'Program.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      results = {}
      for _ in ( 0, 1 ): # First call always returns blank for some reason
        event_data = self._BuildRequest( filepath = filepath,
                                         event_name = 'FileReadyToParse',
                                         filetype = 'cs',
                                         contents = contents )

        results = self._app.post_json( '/event_notification', event_data ).json

      assert_that( results,
                   contains(
                     has_entries( {
                       'kind': equal_to( 'ERROR' ),
                       'text': contains_string(
                           "Unexpected symbol `}'', expecting identifier" ),
                       'location': has_entries( {
                         'line_num': 11,
                         'column_num': 2
                       } ),
                       'location_extent': has_entries( {
                         'start': has_entries( {
                           'line_num': 11,
                           'column_num': 2,
                         } ),
                         'end': has_entries( {
                           'line_num': 11,
                           'column_num': 2,
                         } ),
                       } )
                     } ) ) )


  def Diagnostic_MultipleSolution_test( self ):
    filepaths = [ self._PathToTestFile( 'testy', 'Program.cs' ),
                  self._PathToTestFile( 'testy-multiple-solutions',
                                        'solution-named-like-folder',
                                        'testy',
                                        'Program.cs' ) ]
    lines = [ 11, 10 ]
    for filepath, line in zip( filepaths, lines ):
      with self._WrapOmniSharpServer( filepath ):
        contents = ReadFile( filepath )

        results = {}
        for _ in ( 0, 1 ): # First call always returns blank for some reason
          event_data = self._BuildRequest( filepath = filepath,
                                           event_name = 'FileReadyToParse',
                                           filetype = 'cs',
                                           contents = contents )

          results = self._app.post_json( '/event_notification',
                                         event_data ).json

        assert_that( results,
                     contains(
                       has_entries( {
                           'kind': equal_to( 'ERROR' ),
                           'text': contains_string( "Unexpected symbol `}'', "
                                                    "expecting identifier" ),
                           'location': has_entries( {
                             'line_num': line,
                             'column_num': 2
                           } ),
                           'location_extent': has_entries( {
                             'start': has_entries( {
                               'line_num': line,
                               'column_num': 2,
                             } ),
                             'end': has_entries( {
                               'line_num': line,
                               'column_num': 2,
                             } ),
                           } )
                       } ) ) )


  def Diagnostic_Basic_test( self ):
    filepath = self._PathToTestFile( 'testy', 'Program.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      event_data = self._BuildRequest( filepath = filepath,
                                       event_name = 'FileReadyToParse',
                                       filetype = 'cs',
                                       contents = contents )
      self._app.post_json( '/event_notification', event_data )

      diag_data = self._BuildRequest( filepath = filepath,
                                      filetype = 'cs',
                                      contents = contents,
                                      line_num = 11,
                                      column_num = 2 )

      results = self._app.post_json( '/detailed_diagnostic', diag_data ).json
      assert_that( results,
                   has_entry(
                     'message',
                     contains_string(
                       "Unexpected symbol `}'', expecting identifier" ) ) )


  def Subcommand_GoTo_Basic_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GotoTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      goto_data = self._BuildRequest( completer_target = 'filetype_default',
                                      command_arguments = [ 'GoTo' ],
                                      line_num = 9,
                                      column_num = 15,
                                      contents = contents,
                                      filetype = 'cs',
                                      filepath = filepath )

      eq_( {
        'filepath': self._PathToTestFile( 'testy', 'Program.cs' ),
        'line_num': 7,
        'column_num': 3
      }, self._app.post_json( '/run_completer_command', goto_data ).json )


  def Subcommand_GoToImplementation_Basic_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GotoTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      goto_data = self._BuildRequest(
        completer_target = 'filetype_default',
        command_arguments = [ 'GoToImplementation' ],
        line_num = 13,
        column_num = 13,
        contents = contents,
        filetype = 'cs',
        filepath = filepath
      )

      eq_( {
        'filepath': self._PathToTestFile( 'testy', 'GotoTestCase.cs' ),
        'line_num': 30,
        'column_num': 3
      }, self._app.post_json( '/run_completer_command', goto_data ).json )


  def Subcommand_GoToImplementation_NoImplementation_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GotoTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      goto_data = self._BuildRequest(
        completer_target = 'filetype_default',
        command_arguments = [ 'GoToImplementation' ],
        line_num = 17,
        column_num = 13,
        contents = contents,
        filetype = 'cs',
        filepath = filepath
      )

      try:
        self._app.post_json( '/run_completer_command', goto_data ).json
        raise Exception("Expected a 'No implementations found' error")
      except AppError as e:
        if 'No implementations found' in str(e):
          pass
        else:
          raise


  def Subcommand_GoToImplementation_InvalidLocation_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GotoTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      goto_data = self._BuildRequest(
        completer_target = 'filetype_default',
        command_arguments = [ 'GoToImplementation' ],
        line_num = 2,
        column_num = 1,
        contents = contents,
        filetype = 'cs',
        filepath = filepath
      )

      try:
        self._app.post_json( '/run_completer_command', goto_data ).json
        raise Exception( 'Expected a "Can\\\'t jump to implementation" error' )
      except AppError as e:
        if 'Can\\\'t jump to implementation' in str(e):
          pass
        else:
          raise


  def Subcommand_GoToImplementationElseDeclaration_NoImplementation_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GotoTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      goto_data = self._BuildRequest(
        completer_target = 'filetype_default',
        command_arguments = [ 'GoToImplementationElseDeclaration' ],
        line_num = 17,
        column_num = 13,
        contents = contents,
        filetype = 'cs',
        filepath = filepath
      )

      eq_( {
        'filepath': self._PathToTestFile( 'testy', 'GotoTestCase.cs' ),
        'line_num': 35,
        'column_num': 3
      }, self._app.post_json( '/run_completer_command', goto_data ).json )


  def Subcommand_GoToImplementationElseDeclaration_SingleImplementation_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GotoTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      goto_data = self._BuildRequest(
        completer_target = 'filetype_default',
        command_arguments = [ 'GoToImplementationElseDeclaration' ],
        line_num = 13,
        column_num = 13,
        contents = contents,
        filetype = 'cs',
        filepath = filepath
      )

      eq_( {
        'filepath': self._PathToTestFile( 'testy', 'GotoTestCase.cs' ),
        'line_num': 30,
        'column_num': 3
      }, self._app.post_json( '/run_completer_command', goto_data ).json )


  def Subcommand_GoToImplementationElseDeclaration_MultipleImplementations_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GotoTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      goto_data = self._BuildRequest(
        completer_target = 'filetype_default',
        command_arguments = [ 'GoToImplementationElseDeclaration' ],
        line_num = 21,
        column_num = 13,
        contents = contents,
        filetype = 'cs',
        filepath = filepath
      )

      eq_( [ {
        'filepath': self._PathToTestFile( 'testy', 'GotoTestCase.cs' ),
        'line_num': 43,
        'column_num': 3
      }, {
        'filepath': self._PathToTestFile( 'testy', 'GotoTestCase.cs' ),
        'line_num': 48,
        'column_num': 3
      } ], self._app.post_json( '/run_completer_command', goto_data ).json )


  def Subcommand_GetType_EmptyMessage_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GetTypeTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      gettype_data = self._BuildRequest( completer_target = 'filetype_default',
                                         command_arguments = [ 'GetType' ],
                                         line_num = 1,
                                         column_num = 1,
                                         contents = contents,
                                         filetype = 'cs',
                                         filepath = filepath )

      eq_( {
        u'message': u""
      }, self._app.post_json( '/run_completer_command', gettype_data ).json )


  def Subcommand_GetType_VariableDeclaration_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GetTypeTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      gettype_data = self._BuildRequest( completer_target = 'filetype_default',
                                         command_arguments = [ 'GetType' ],
                                         line_num = 4,
                                         column_num = 5,
                                         contents = contents,
                                         filetype = 'cs',
                                         filepath = filepath )

      eq_( {
        u'message': u"string"
      }, self._app.post_json( '/run_completer_command', gettype_data ).json )


  def Subcommand_GetType_VariableUsage_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GetTypeTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      gettype_data = self._BuildRequest( completer_target = 'filetype_default',
                                         command_arguments = [ 'GetType' ],
                                         line_num = 5,
                                         column_num = 5,
                                         contents = contents,
                                         filetype = 'cs',
                                         filepath = filepath )

      eq_( {
        u'message': u"string str"
      }, self._app.post_json( '/run_completer_command', gettype_data ).json )


  def Subcommand_GetType_Constant_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GetTypeTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      gettype_data = self._BuildRequest( completer_target = 'filetype_default',
                                         command_arguments = [ 'GetType' ],
                                         line_num = 4,
                                         column_num = 14,
                                         contents = contents,
                                         filetype = 'cs',
                                         filepath = filepath )

      eq_( {
        u'message': u"System.String"
      }, self._app.post_json( '/run_completer_command', gettype_data ).json )


  def Subcommand_GetType_DocsIgnored_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GetTypeTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      gettype_data = self._BuildRequest( completer_target = 'filetype_default',
                                         command_arguments = [ 'GetType' ],
                                         line_num = 9,
                                         column_num = 34,
                                         contents = contents,
                                         filetype = 'cs',
                                         filepath = filepath )

      eq_( {
        u'message': u"int GetTypeTestCase.an_int_with_docs;",
      }, self._app.post_json( '/run_completer_command', gettype_data ).json )


  def Subcommand_GetDoc_Variable_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GetDocTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      getdoc_data = self._BuildRequest( completer_target = 'filetype_default',
                                        command_arguments = [ 'GetDoc' ],
                                        line_num = 13,
                                        column_num = 28,
                                        contents = contents,
                                        filetype = 'cs',
                                        filepath = filepath )

      eq_( {
        'detailed_info': 'int GetDocTestCase.an_int;\n'
                         'an integer, or something',
      }, self._app.post_json( '/run_completer_command', getdoc_data ).json )


  def Subcommand_GetDoc_Function_test( self ):
    filepath = self._PathToTestFile( 'testy', 'GetDocTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      getdoc_data = self._BuildRequest( completer_target = 'filetype_default',
                                        command_arguments = [ 'GetDoc' ],
                                        line_num = 33,
                                        column_num = 27,
                                        contents = contents,
                                        filetype = 'cs',
                                        filepath = filepath )

      # It seems that Omnisharp server eats newlines
      eq_( {
        'detailed_info': 'int GetDocTestCase.DoATest();\n'
                         ' Very important method. With multiple lines of '
                         'commentary And Format- -ting',
      }, self._app.post_json( '/run_completer_command', getdoc_data ).json )


  def _RunFixIt( self, line, column, expected_result ):
    filepath = self._PathToTestFile( 'testy', 'FixItTestCase.cs' )
    with self._WrapOmniSharpServer( filepath ):
      contents = ReadFile( filepath )

      fixit_data = self._BuildRequest( completer_target = 'filetype_default',
                                       command_arguments = [ 'FixIt' ],
                                       line_num = line,
                                       column_num = column,
                                       contents = contents,
                                       filetype = 'cs',
                                       filepath = filepath )

      eq_( expected_result,
           self._app.post_json( '/run_completer_command', fixit_data ).json )


  def Subcommand_FixIt_RemoveSingleLine_test( self ):
    filepath = self._PathToTestFile( 'testy', 'FixItTestCase.cs' )
    self._RunFixIt( 11, 1, {
      u'fixits': [
        {
          u'location': {
            u'line_num': 11,
            u'column_num': 1,
            u'filepath': filepath
          },
          u'chunks': [
            {
              u'replacement_text': '',
              u'range': {
                u'start': {
                  u'line_num': 10,
                  u'column_num': 20,
                  u'filepath': filepath
                },
                u'end': {
                  u'line_num': 11,
                  u'column_num': 30,
                  u'filepath': filepath
                },
              }
            }
          ]
        }
      ]
    } )


  def Subcommand_FixIt_MultipleLines_test( self ):
    filepath = self._PathToTestFile( 'testy', 'FixItTestCase.cs' )
    self._RunFixIt( 19, 1, {
      u'fixits': [
        {
          u'location': {
            u'line_num': 19,
            u'column_num': 1,
            u'filepath': filepath
          },
          u'chunks': [
            {
              u'replacement_text': "return On",
              u'range': {
                u'start': {
                  u'line_num': 20,
                  u'column_num': 13,
                  u'filepath': filepath
                },
                u'end': {
                  u'line_num': 21,
                  u'column_num': 35,
                  u'filepath': filepath
                },
              }
            }
          ]
        }
      ]
    } )


  def Subcommand_FixIt_SpanFileEdge_test( self ):
    filepath = self._PathToTestFile( 'testy', 'FixItTestCase.cs' )
    self._RunFixIt( 1, 1, {
      u'fixits': [
        {
          u'location': {
            u'line_num': 1,
            u'column_num': 1,
            u'filepath': filepath
          },
          u'chunks': [
            {
              u'replacement_text': 'System',
              u'range': {
                u'start': {
                  u'line_num': 1,
                  u'column_num': 7,
                  u'filepath': filepath
                },
                u'end': {
                  u'line_num': 3,
                  u'column_num': 18,
                  u'filepath': filepath
                },
              }
            }
          ]
        }
      ]
    } )


  def Subcommand_FixIt_AddTextInLine_test( self ):
    filepath = self._PathToTestFile( 'testy', 'FixItTestCase.cs' )
    self._RunFixIt( 9, 1, {
      u'fixits': [
        {
          u'location': {
            u'line_num': 9,
            u'column_num': 1,
            u'filepath': filepath
          },
          u'chunks': [
            {
              u'replacement_text': ', StringComparison.Ordinal',
              u'range': {
                u'start': {
                  u'line_num': 9,
                  u'column_num': 29,
                  u'filepath': filepath
                },
                u'end': {
                  u'line_num': 9,
                  u'column_num': 29,
                  u'filepath': filepath
                },
              }
            }
          ]
        }
      ]
    } )


  def Subcommand_FixIt_ReplaceTextInLine_test( self ):
    filepath = self._PathToTestFile( 'testy', 'FixItTestCase.cs' )
    self._RunFixIt( 10, 1, {
      u'fixits': [
        {
          u'location': {
            u'line_num': 10,
            u'column_num': 1,
            u'filepath': filepath
          },
          u'chunks': [
            {
              u'replacement_text': 'const int',
              u'range': {
                u'start': {
                  u'line_num': 10,
                  u'column_num': 13,
                  u'filepath': filepath
                },
                u'end': {
                  u'line_num': 10,
                  u'column_num': 16,
                  u'filepath': filepath
                },
              }
            }
          ]
        }
      ]
    } )
