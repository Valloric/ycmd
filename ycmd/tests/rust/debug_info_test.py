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

from hamcrest import assert_that, matches_regexp

from ycmd.tests.rust import IsolatedYcmd, SharedYcmd
from ycmd.tests.test_utils import BuildRequest, StopCompleterServer, UserOption


@SharedYcmd
def DebugInfo_ServerIsRunning_test( app ):
  request_data = BuildRequest( filetype = 'rust' )
  assert_that(
    app.post_json( '/debug_info', request_data ).json,
    matches_regexp( 'Rust completer debug information:\n'
                    '  Racerd running at: http://127.0.0.1:\d+\n'
                    '  Racerd process ID: \d+\n'
                    '  Racerd executable: .+\n'
                    '  Racerd logfiles:\n'
                    '    .+\n'
                    '    .+\n'
                    '  Rust sources: .+' ) )


@IsolatedYcmd
def DebugInfo_ServerIsNotRunning_LogfilesExist_test( app ):
  with UserOption( 'keep_logfiles', True ):
    StopCompleterServer( app, 'rust' )
    request_data = BuildRequest( filetype = 'rust' )
    assert_that(
      app.post_json( '/debug_info', request_data ).json,
      matches_regexp( 'Rust completer debug information:\n'
                      '  Racerd no longer running\n'
                      '  Racerd executable: .+\n'
                      '  Racerd logfiles:\n'
                      '    .+\n'
                      '    .+\n'
                      '  Rust sources: .+' ) )


@IsolatedYcmd
def DebugInfo_ServerIsNotRunning_LogfilesDoNotExist_test( app ):
  with UserOption( 'keep_logfiles', False ):
    StopCompleterServer( app, 'rust' )
    request_data = BuildRequest( filetype = 'rust' )
    assert_that(
      app.post_json( '/debug_info', request_data ).json,
      matches_regexp( 'Rust completer debug information:\n'
                      '  Racerd is not running\n'
                      '  Racerd executable: .+\n'
                      '  Rust sources: .+' ) )
