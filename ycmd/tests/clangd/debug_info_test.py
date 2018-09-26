# Copyright (C) 2011-2012 Google Inc.
#               2017      ycmd contributors
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
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

import os
from hamcrest import ( assert_that, contains, empty, has_entries, has_entry )

from ycmd.tests.clangd import ( IsolatedYcmd, PathToTestFile, SharedYcmd,
                               TemporaryClangProject )
from ycmd.tests.test_utils import BuildRequest, TemporaryTestDir


@SharedYcmd
def DebugInfo_FlagsWhenNoCompilationDatabase_test( app ):
  request_data = BuildRequest( filepath = PathToTestFile( 'basic.cpp' ),
                               filetype = 'cpp' )
  assert_that(
    app.post_json( '/debug_info', request_data ).json,
    has_entry( 'completer', has_entries( {
      'name': 'clangd',
      'servers': contains( has_entries( {
          'name': 'clangd',
          'pid': None,
          'is_running': False
      } ) ),
      'items': empty()
    } ) )
  )


@IsolatedYcmd()
def DebugInfo_FlagsWhenCompilationDatabaseLoaded_test( app ):
  with TemporaryTestDir() as tmp_dir:
    compile_commands = [
      {
        'directory': tmp_dir,
        'command': 'clang++ -I. -I/absolute/path -Wall',
        'file': os.path.join( tmp_dir, 'test.cc' ),
      },
    ]
    with TemporaryClangProject( tmp_dir, compile_commands ):
      request_data = BuildRequest(
        filepath = os.path.join( tmp_dir, 'test.cc' ),
        filetype = 'cpp' )

      assert_that(
        app.post_json( '/debug_info', request_data ).json,
        has_entry( 'completer', has_entries( {
          'name': 'clangd',
          'servers': contains( has_entries( {
              'name': 'clangd',
              'pid': None,
              'is_running': False
          } ) ),
          'items': empty()
        } ) )
      )
