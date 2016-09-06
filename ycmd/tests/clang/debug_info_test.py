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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from hamcrest import ( assert_that, contains, empty, has_entries, has_entry,
                       matches_regexp )

from ycmd.tests.clang import IsolatedYcmd, PathToTestFile, SharedYcmd
from ycmd.tests.test_utils import BuildRequest


@SharedYcmd
def DebugInfo_FlagsWhenExtraConfLoaded_test( app ):
  app.post_json( '/load_extra_conf_file',
                 { 'filepath': PathToTestFile( '.ycm_extra_conf.py' ) } )
  request_data = BuildRequest( filepath = PathToTestFile( 'basic.cpp' ),
                               filetype = 'cpp' )
  assert_that(
    app.post_json( '/debug_info', request_data ).json,
    has_entry( 'completer', has_entries( {
      'name': 'C-family',
      'servers': empty(),
      'items': contains( has_entries( {
        'description': 'flags',
        'value': matches_regexp( "\['-x', 'c\+\+', .*\]" )
      } ) )
    } ) )
  )


@SharedYcmd
def DebugInfo_FlagsWhenNoExtraConfFound_test( app ):
  request_data = BuildRequest( filetype = 'cpp' )
  # First request, FlagsForFile raises a NoExtraConfDetected exception.
  assert_that(
    app.post_json( '/debug_info', request_data ).json,
    has_entry( 'completer', has_entries( {
      'name': 'C-family',
      'servers': empty(),
      'items': contains( has_entries( {
        'description': 'flags',
        'value': '[]'
      } ) )
    } ) )
  )
  # Second request, FlagsForFile returns None.
  assert_that(
    app.post_json( '/debug_info', request_data ).json,
    has_entry( 'completer', has_entries( {
      'name': 'C-family',
      'servers': empty(),
      'items': contains( has_entries( {
        'description': 'flags',
        'value': '[]'
      } ) )
    } ) )
  )


@IsolatedYcmd
def DebugInfo_FlagsWhenExtraConfFoundButNotLoaded_test( app ):
  request_data = BuildRequest( filepath = PathToTestFile( 'basic.cpp' ),
                               filetype = 'cpp' )
  assert_that(
    app.post_json( '/debug_info', request_data ).json,
    has_entry( 'completer', has_entries( {
      'name': 'C-family',
      'servers': empty(),
      'items': contains( has_entries( {
        'description': 'flags',
        'value': '[]'
      } ) )
    } ) )
  )
