#!/usr/bin/env python
#
# Copyright (C) 2015 ycmd contributors.
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

from hamcrest import ( assert_that, contains, contains_string, equal_to,
                       has_entries, has_entry )
from .cs_handlers_test import Cs_Handlers_test


class Cs_Diagnostics_test( Cs_Handlers_test ):

  def ZeroBasedLineAndColumn_test( self ):
    yield self._ZeroBasedLineAndColumn_test, True
    yield self._ZeroBasedLineAndColumn_test, False


  def _ZeroBasedLineAndColumn_test( self, use_roslyn ):
    filepath = self._PathToTestFile( 'testy', 'Program.cs' )
    contents = open( filepath ).read()
    self._UseRoslynOmnisharp( filepath, use_roslyn )
    event_data = self._BuildRequest( filepath = filepath,
                                     filetype = 'cs',
                                     contents = contents,
                                     event_name = 'FileReadyToParse' )

    results = self._app.post_json( '/event_notification', event_data )
    self._WaitUntilOmniSharpServerReady( filepath )

    event_data = self._BuildRequest( filepath = filepath,
                                     event_name = 'FileReadyToParse',
                                     filetype = 'cs',
                                     contents = contents )

    results = self._app.post_json( '/event_notification', event_data ).json

    try:
      assert_that( results,
      _Diagnostics_ExpectedResult( use_roslyn, True ) )
    finally:
        self._StopOmniSharpServer( filepath )


  def MultipleSolution_test( self ):
    yield self._MultipleSolution_test, True
    yield self._MultipleSolution_test, False


  def _MultipleSolution_test( self, use_roslyn ):
    filepaths = [ self._PathToTestFile( 'testy', 'Program.cs' ),
                  self._PathToTestFile( 'testy-multiple-solutions',
                                        'solution-named-like-folder',
                                        'testy',
                                        'Program.cs' ) ]
    main_errors = [ True, False ]
    for filepath, main_error in zip( filepaths, main_errors ):
      contents = open( filepath ).read()
      self._UseRoslynOmnisharp( filepath, use_roslyn )
      event_data = self._BuildRequest( filepath = filepath,
                                       filetype = 'cs',
                                       contents = contents,
                                       event_name = 'FileReadyToParse' )

      results = self._app.post_json( '/event_notification', event_data )
      self._WaitUntilOmniSharpServerReady( filepath )

      event_data = self._BuildRequest( filepath = filepath,
                                       event_name = 'FileReadyToParse',
                                       filetype = 'cs',
                                       contents = contents )

      results = self._app.post_json( '/event_notification', event_data ).json

      try:
        assert_that( results,
          _Diagnostics_ExpectedResult( use_roslyn, main_error ) )
      finally:
        self._StopOmniSharpServer( filepath )


  # This test seems identical to ZeroBasedLineAndColumn one
  def Basic_test( self ):
    yield self._Basic_test, True
    yield self._Basic_test, False


  def _Basic_test( self, use_roslyn ):
    filepath = self._PathToTestFile( 'testy', 'Program.cs' )
    contents = open( filepath ).read()
    self._UseRoslynOmnisharp( filepath, use_roslyn )
    event_data = self._BuildRequest( filepath = filepath,
                                     filetype = 'cs',
                                     contents = contents,
                                     event_name = 'FileReadyToParse' )

    self._app.post_json( '/event_notification', event_data )
    self._WaitUntilOmniSharpServerReady( filepath )
    self._app.post_json( '/event_notification', event_data )

    diag_data = self._BuildRequest( filepath = filepath,
                                    filetype = 'cs',
                                    contents = contents,
                                    line_num = 11,
                                    column_num = 2 )

    results = self._app.post_json( '/detailed_diagnostic', diag_data ).json
    expected = ( u"'Console' does not contain a definition for ''" if use_roslyn
                 else "Unexpected symbol `}'', expecting identifier" )
  
    try:
      assert_that( results,
                  has_entry(
                        'message',
                        contains_string( expected ) ) )
    finally:
        self._StopOmniSharpServer( filepath )


def _Diagnostics_ExpectedResult( use_roslyn, flag ):
  def build_matcher( kind, message, line, column ):
    return has_entries( {
      'kind': equal_to( kind ),
      'text': contains_string( message ),
      'location': has_entries( {
        'line_num': line,
        'column_num': column
      } ),
      'location_extent': has_entries( {
        'start': has_entries( {
          'line_num': line,
          'column_num': column
        } ),
        'end': has_entries( {
          'line_num': line,
          'column_num': column
        } ),
      } )
    } )
  entries = []
  if use_roslyn:
    entries.append(
      build_matcher( 'ERROR', "Identifier expected", 10, 12 )
    )
    entries.append(
      build_matcher( 'ERROR', "; expected", 10, 12 ),
  )
    entries.append(
      build_matcher( 'ERROR',
        "'Console' does not contain a definition for ''", 11, 1 ),
    )
    entries.append(
      build_matcher( 'WARNING',
        "is assigned but its value is never used", 9, 8 ),
    )
    if flag:
      entries.append(
        build_matcher( 'ERROR',
          "Program has more than one entry point defined. Compile with /main to "
          +"specify the type that contains the entry point.", 7, 22 ),
      )
  else:
    entries.append(
      build_matcher( 'ERROR', "Unexpected symbol `}'', expecting identifier", 11, 2 )
    )
  return contains( *entries )
