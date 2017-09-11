# Copyright (C) 2017 ycmd contributors
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

from hamcrest import ( assert_that,
                       contains,
                       contains_inanyorder,
                       empty,
                       has_entries )
from nose.tools import eq_

from pprint import pformat
import requests

from ycmd.tests.java import ( PathToTestFile, SharedYcmd )
from ycmd.tests.test_utils import ( BuildRequest,
                                    CompletionEntryMatcher )
from ycmd.utils import ReadFile


def _CombineRequest( request, data ):
  return BuildRequest( **_Merge( request, data ) )


def _Merge( request, data ):
  kw = dict( request )
  kw.update( data )
  return kw


def RunTest( app, test ):
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

  app.post_json( '/event_notification',
                 _CombineRequest( test[ 'request' ], {
                                  'event_name': 'FileReadyToParse',
                                  'contents': contents,
                                  } ),
                 expect_errors = True )

  # We ignore errors here and we check the response code ourself.
  # This is to allow testing of requests returning errors.
  response = app.post_json( '/completions',
                            _CombineRequest( test[ 'request' ], {
                               'contents': contents
                            } ),
                            expect_errors = True )

  print( 'completer response: {0}'.format( pformat( response.json ) ) )

  eq_( response.status_code, test[ 'expect' ][ 'response' ] )

  assert_that( response.json, test[ 'expect' ][ 'data' ] )


OBJECT_METHODS = [
  CompletionEntryMatcher( 'equals', 'Object' ),
  CompletionEntryMatcher( 'getClass', 'Object' ),
  CompletionEntryMatcher( 'hashCode', 'Object' ),
  CompletionEntryMatcher( 'notify', 'Object' ),
  CompletionEntryMatcher( 'notifyAll', 'Object' ),
  CompletionEntryMatcher( 'toString', 'Object' ),
  CompletionEntryMatcher( 'wait', 'Object', {
    'menu_text': 'wait(long timeout, int nanos) : void',
  } ),
  CompletionEntryMatcher( 'wait', 'Object', {
    'menu_text': 'wait(long timeout) : void',
  } ),
  CompletionEntryMatcher( 'wait', 'Object', {
    'menu_text': 'wait() : void',
  } ),
]


# The zealots that designed java made everything inherit from Object (except,
# possibly Object, or Class, or whichever one they used to break the Smalltalk
# infinite recursion problem). Anyway, that means that we get a lot of noise
# suggestions from the Object Class interface. This allows us to write:
#
#   contains_inanyorder( *WithObjectMethods( CompletionEntryMatcher( ... ) ) )
#
# and focus on what we care about.
def WithObjectMethods( *args ):
  return list( OBJECT_METHODS ) + list( args )


@SharedYcmd
def GetCompletions_NoQuery_test( app ):
  RunTest( app, {
    'description': 'semantic completion works for builtin types (no query)',
    'request': {
      'filetype'  : 'java',
      'filepath'  : PathToTestFile( 'simple_eclipse_project',
                                    'src',
                                    'com',
                                    'test',
                                    'TestFactory.java' ),
      'line_num'  : 27,
      'column_num': 12,
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'completions': contains_inanyorder(
          *WithObjectMethods(
            CompletionEntryMatcher( 'test', 'TestFactory.Bar' ),
            CompletionEntryMatcher( 'testString', 'TestFactory.Bar' )
          )
        ),
        'errors': empty(),
      } )
    },
  } )


@SharedYcmd
def GetCompletions_WithQuery_test( app ):
  RunTest( app, {
    'description': 'semantic completion works for builtin types (no query)',
    'request': {
      'filetype'  : 'java',
      'filepath'  : PathToTestFile( 'simple_eclipse_project',
                                    'src',
                                    'com',
                                    'test',
                                    'TestFactory.java' ),
      'line_num'  : 27,
      'column_num': 15,
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'completions': contains_inanyorder(
            CompletionEntryMatcher( 'test', 'TestFactory.Bar' ),
            CompletionEntryMatcher( 'testString', 'TestFactory.Bar' )
        ),
        'errors': empty(),
      } )
    },
  } )


@SharedYcmd
def GetCompletions_WithSnippet_test( app ):
  RunTest( app, {
    'description': 'semantic completion works for builtin types (no query)',
    'request': {
      'filetype'  : 'java',
      'filepath'  : PathToTestFile( 'simple_eclipse_project',
                                    'src',
                                    'com',
                                    'test',
                                    'TestFactory.java' ),
      'line_num'  : 19,
      'column_num': 25,
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'completions': contains_inanyorder( CompletionEntryMatcher(
          'CUTHBERT',
          'com.test.wobble.Wibble',
          # FIXME: Replace with ChunkMatcher, LocationMatcher, etc.
          {
            'extra_data': has_entries( {
              'fixits': contains( has_entries( {
                'chunks': contains(
                  # For some reason, jdtls feels it's OK to replace the text
                  # before the cursor. Perhaps it does this to canonicalise the
                  # path ?
                  has_entries( {
                    'replacement_text': 'Wibble',
                    'range': has_entries( {
                      'start': has_entries( {
                        'line_num': 19,
                        'column_num': 15,
                      } ),
                      'end': has_entries( {
                        'line_num': 19,
                        'column_num': 21,
                      } )
                    } ),
                  } ),
                  # When doing an import, eclipse likes to add two newlines
                  # after the package. I suppose this is config in real eclipse,
                  # but there's no mechanism to configure this in jdtl afaik.
                  has_entries( {
                    'replacement_text': '\n\n',
                    'range': has_entries( {
                      'start': has_entries( {
                        'line_num': 1,
                        'column_num': 18,
                      } ),
                      'end': has_entries( {
                        'line_num': 1,
                        'column_num': 18,
                      } )
                    } ),
                  } ),
                  # OK, so it inserts the import
                  has_entries( {
                    'replacement_text': 'import com.test.wobble.Wibble;',
                    'range': has_entries( {
                      'start': has_entries( {
                        'line_num': 1,
                        'column_num': 18,
                      } ),
                      'end': has_entries( {
                        'line_num': 1,
                        'column_num': 18,
                      } )
                    } ),
                  } ),
                  # More newlines. Who doesn't like newlines?!
                  has_entries( {
                    'replacement_text': '\n\n',
                    'range': has_entries( {
                      'start': has_entries( {
                        'line_num': 1,
                        'column_num': 18,
                      } ),
                      'end': has_entries( {
                        'line_num': 1,
                        'column_num': 18,
                      } )
                    } ),
                  } ),
                  # For reasons known only to the eclipse JDT developers, it
                  # seems to want to delete the lines after the package first.
                  #
                  has_entries( {
                    'replacement_text': '',
                    'range': has_entries( {
                      'start': has_entries( {
                        'line_num': 1,
                        'column_num': 18,
                      } ),
                      'end': has_entries( {
                        'line_num': 3,
                        'column_num': 1,
                      } )
                    } ),
                  } ),
                ),
              } ) ),
            } ),
          } ),
        ),
        'errors': empty(),
      } )
    },
  } )
