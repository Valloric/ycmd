# Copyright (C) 2017 ycmd contributors
# encoding: utf-8
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

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

import time
import json
from future.utils import iterkeys
from hamcrest import ( assert_that,
                       contains,
                       contains_inanyorder,
                       has_entries,
                       has_item )
from nose.tools import eq_

from ycmd.tests.java import ( DEFAULT_PROJECT_DIR,
                              IsolatedYcmd,
                              PathToTestFile,
                              PollForMessages,
                              PollForMessagesTimeoutException,
                              SharedYcmd,
                              StartJavaCompleterServerInDirectory )

from ycmd.tests.test_utils import BuildRequest, LocationMatcher
from ycmd.utils import ReadFile

from pprint import pformat
from mock import patch
from ycmd.completers.language_server import language_server_protocol as lsp



def RangeMatch( filepath, start, end ):
  return has_entries( {
    'start': LocationMatcher( filepath, *start ),
    'end': LocationMatcher( filepath, *end ),
  } )


def ProjectPath( *args ):
  return PathToTestFile( DEFAULT_PROJECT_DIR,
                         'src',
                         'com',
                         'test',
                         *args )


InternalNonProjectFile = PathToTestFile( DEFAULT_PROJECT_DIR, 'test.java' )
TestFactory = ProjectPath( 'TestFactory.java' )
TestLauncher = ProjectPath( 'TestLauncher.java' )
TestWidgetImpl = ProjectPath( 'TestWidgetImpl.java' )
youcompleteme_Test = PathToTestFile( DEFAULT_PROJECT_DIR,
                                     'src',
                                     'com',
                                     'youcompleteme',
                                     'Test.java' )

DIAG_MATCHERS_PER_FILE = {
  InternalNonProjectFile: [],
  TestFactory: contains_inanyorder(
    has_entries( {
      'kind': 'WARNING',
      'text': 'The value of the field TestFactory.Bar.testString is not used',
      'location': LocationMatcher( TestFactory, 15, 19 ),
      'location_extent': RangeMatch( TestFactory, ( 15, 19 ), ( 15, 29 ) ),
      'ranges': contains( RangeMatch( TestFactory, ( 15, 19 ), ( 15, 29 ) ) ),
      'fixit_available': False
    } ),
    has_entries( {
      'kind': 'ERROR',
      'text': 'Wibble cannot be resolved to a type',
      'location': LocationMatcher( TestFactory, 18, 24 ),
      'location_extent': RangeMatch( TestFactory, ( 18, 24 ), ( 18, 30 ) ),
      'ranges': contains( RangeMatch( TestFactory, ( 18, 24 ), ( 18, 30 ) ) ),
      'fixit_available': False
    } ),
    has_entries( {
      'kind': 'ERROR',
      'text': 'Wibble cannot be resolved to a variable',
      'location': LocationMatcher( TestFactory, 19, 15 ),
      'location_extent': RangeMatch( TestFactory, ( 19, 15 ), ( 19, 21 ) ),
      'ranges': contains( RangeMatch( TestFactory, ( 19, 15 ), ( 19, 21 ) ) ),
      'fixit_available': False
    } ),
    has_entries( {
      'kind': 'ERROR',
      'text': 'Type mismatch: cannot convert from int to boolean',
      'location': LocationMatcher( TestFactory, 27, 10 ),
      'location_extent': RangeMatch( TestFactory, ( 27, 10 ), ( 27, 16 ) ),
      'ranges': contains( RangeMatch( TestFactory, ( 27, 10 ), ( 27, 16 ) ) ),
      'fixit_available': False
    } ),
    has_entries( {
      'kind': 'ERROR',
      'text': 'Type mismatch: cannot convert from int to boolean',
      'location': LocationMatcher( TestFactory, 30, 10 ),
      'location_extent': RangeMatch( TestFactory, ( 30, 10 ), ( 30, 16 ) ),
      'ranges': contains( RangeMatch( TestFactory, ( 30, 10 ), ( 30, 16 ) ) ),
      'fixit_available': False
    } ),
    has_entries( {
      'kind': 'ERROR',
      'text': 'The method doSomethingVaguelyUseful() in the type '
              'AbstractTestWidget is not applicable for the arguments '
              '(TestFactory.Bar)',
      'location': LocationMatcher( TestFactory, 30, 23 ),
      'location_extent': RangeMatch( TestFactory, ( 30, 23 ), ( 30, 47 ) ),
      'ranges': contains( RangeMatch( TestFactory, ( 30, 23 ), ( 30, 47 ) ) ),
      'fixit_available': False
    } ),
  ),
  TestWidgetImpl: contains_inanyorder(
    has_entries( {
      'kind': 'WARNING',
      'text': 'The value of the local variable a is not used',
      'location': LocationMatcher( TestWidgetImpl, 15, 9 ),
      'location_extent': RangeMatch( TestWidgetImpl, ( 15, 9 ), ( 15, 10 ) ),
      'ranges': contains( RangeMatch( TestWidgetImpl, ( 15, 9 ), ( 15, 10 ) ) ),
      'fixit_available': False
    } ),
  ),
  TestLauncher: contains_inanyorder (
    has_entries( {
      'kind': 'ERROR',
      'text': 'The type new TestLauncher.Launchable(){} must implement the '
              'inherited abstract method TestLauncher.Launchable.launch('
              'TestFactory)',
      'location': LocationMatcher( TestLauncher, 28, 16 ),
      'location_extent': RangeMatch( TestLauncher, ( 28, 16 ), ( 28, 28 ) ),
      'ranges': contains( RangeMatch( TestLauncher, ( 28, 16 ), ( 28, 28 ) ) ),
      'fixit_available': False
    } ),
    has_entries( {
      'kind': 'ERROR',
      'text': 'The method launch() of type new TestLauncher.Launchable(){} '
              'must override or implement a supertype method',
      'location': LocationMatcher( TestLauncher, 30, 19 ),
      'location_extent': RangeMatch( TestLauncher, ( 30, 19 ), ( 30, 27 ) ),
      'ranges': contains( RangeMatch( TestLauncher, ( 30, 19 ), ( 30, 27 ) ) ),
      'fixit_available': False
    } ),
    has_entries( {
      'kind': 'ERROR',
      'text': 'Cannot make a static reference to the non-static field factory',
      'location': LocationMatcher( TestLauncher, 31, 32 ),
      'location_extent': RangeMatch( TestLauncher, ( 31, 32 ), ( 31, 39 ) ),
      'ranges': contains( RangeMatch( TestLauncher, ( 31, 32 ), ( 31, 39 ) ) ),
      'fixit_available': False
    } ),
  ),
  youcompleteme_Test: contains(
    has_entries( {
      'kind': 'ERROR',
      'text': 'The method doUnicødeTes() in the type Test is not applicable '
              'for the arguments (String)',
      'location': LocationMatcher( youcompleteme_Test, 13, 10 ),
      'location_extent': RangeMatch( youcompleteme_Test,
                                     ( 13, 10 ),
                                     ( 13, 23 ) ),
      'ranges': contains( RangeMatch( youcompleteme_Test,
                                      ( 13, 10 ),
                                      ( 13, 23 ) ) ),
      'fixit_available': False
    } ),
  ),
}


@SharedYcmd
def FileReadyToParse_Diagnostics_Simple_test( app ):
  filepath = ProjectPath( 'TestFactory.java' )
  contents = ReadFile( filepath )

  # It can take a while for the diagnostics to be ready
  for tries in range( 0, 10 ):
    event_data = BuildRequest( event_name = 'FileReadyToParse',
                               contents = contents,
                               filepath = filepath,
                               filetype = 'java' )

    results = app.post_json( '/event_notification', event_data ).json

    if results:
      break

    time.sleep( 0.5 )


  print( 'completer response: {0}'.format( pformat( results ) ) )

  assert_that( results, DIAG_MATCHERS_PER_FILE[ filepath ] )


@IsolatedYcmd
def FileReadyToParse_Diagnostics_FileNotOnDisk_test( app ):
  StartJavaCompleterServerInDirectory( app,
                                       PathToTestFile( DEFAULT_PROJECT_DIR ) )

  contents = '''
    package com.test;
    class Test {
      public String test
    }
  '''
  filepath = ProjectPath( 'Test.java' )

  event_data = BuildRequest( event_name = 'FileReadyToParse',
                             contents = contents,
                             filepath = filepath,
                             filetype = 'java' )

  results = app.post_json( '/event_notification', event_data ).json

  # This is a new file, so the diagnostics can't possibly be available when the
  # initial parse request is sent. We receive these asynchronously.
  eq_( results, {} )

  diag_matcher = contains( has_entries( {
    'kind': 'ERROR',
    'text': 'Syntax error, insert ";" to complete ClassBodyDeclarations',
    'location': LocationMatcher( filepath, 4, 21 ),
    'location_extent': RangeMatch( filepath, ( 4, 21 ), ( 4, 25 ) ),
    'ranges': contains( RangeMatch( filepath, ( 4, 21 ), ( 4, 25 ) ) ),
    'fixit_available': False
  } ) )

  # Poll until we receive the diags
  for message in PollForMessages( app,
                                  { 'filepath': filepath,
                                    'contents': contents } ):
    print( 'Message {0}'.format( pformat( message ) ) )
    if 'diagnostics' in message and message[ 'filepath' ] == filepath:
      assert_that( message, has_entries( {
        'diagnostics': diag_matcher,
        'filepath': filepath
      } ) )
      break

  # Now confirm that we _also_ get these from the FileReadyToParse request
  for tries in range( 0, 10 ):
    results = app.post_json( '/event_notification', event_data ).json
    if results:
      break
    time.sleep( 0.5 )

  print( 'completer response: {0}'.format( pformat( results ) ) )

  assert_that( results, diag_matcher )


@SharedYcmd
def Poll_Diagnostics_ProjectWide_Eclipse_test( app ):
  filepath = ProjectPath( 'TestLauncher.java' )
  contents = ReadFile( filepath )

  # Poll until we receive _all_ the diags asynchronously
  to_see = sorted( iterkeys( DIAG_MATCHERS_PER_FILE ) )
  seen = dict()

  try:
    for message in PollForMessages( app,
                                    { 'filepath': filepath,
                                      'contents': contents } ):
      print( 'Message {0}'.format( pformat( message ) ) )
      if 'diagnostics' in message:
        seen[ message[ 'filepath' ] ] = True
        if message[ 'filepath' ] not in DIAG_MATCHERS_PER_FILE:
          raise AssertionError(
            'Received diagnostics for unexpected file {0}. '
            'Only expected {1}'.format( message[ 'filepath' ], to_see ) )
        assert_that( message, has_entries( {
          'diagnostics': DIAG_MATCHERS_PER_FILE[ message[ 'filepath' ] ],
          'filepath': message[ 'filepath' ]
        } ) )

      if sorted( iterkeys( seen ) ) == to_see:
        break

      # Eventually PollForMessages will throw a timeout exception and we'll fail
      # if we don't see all of the expected diags
  except PollForMessagesTimeoutException as e:
    raise AssertionError(
      str( e ) +
      'Timed out waiting for full set of diagnostics. '
      'Expected to see diags for {0}, but only saw {1}.'.format(
        json.dumps( to_see, indent=2 ),
        json.dumps( sorted( iterkeys( seen ) ), indent=2 ) ) )


@IsolatedYcmd
@patch(
  'ycmd.completers.language_server.language_server_protocol.UriToFilePath',
  side_effect = lsp.InvalidUriException )
def FileReadyToParse_Diagnostics_InvalidURI_test( app, uri_to_filepath, *args ):
  StartJavaCompleterServerInDirectory( app,
                                       PathToTestFile( DEFAULT_PROJECT_DIR ) )

  filepath = ProjectPath( 'TestFactory.java' )
  contents = ReadFile( filepath )

  # It can take a while for the diagnostics to be ready
  for tries in range( 0, 10 ):
    event_data = BuildRequest( event_name = 'FileReadyToParse',
                               contents = contents,
                               filepath = filepath,
                               filetype = 'java' )

    results = app.post_json( '/event_notification', event_data ).json

    if results:
      print( 'got diagnostics on try number {0}'.format( tries ) )
      break

    time.sleep( 0.5 )

  print( 'Completer response: {0}'.format( json.dumps( results, indent=2 ) ) )

  uri_to_filepath.assert_called()

  assert_that( results, has_item(
    has_entries( {
      'kind': 'WARNING',
      'text': 'The value of the field TestFactory.Bar.testString is not used',
      'location': LocationMatcher( '', 15, 19 ),
      'location_extent': RangeMatch( '', ( 15, 19 ), ( 15, 29 ) ),
      'ranges': contains( RangeMatch( '', ( 15, 19 ), ( 15, 29 ) ) ),
      'fixit_available': False
    } ),
  ) )
