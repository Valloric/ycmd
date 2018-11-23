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

"""This test is for utilites used in clangd."""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

from nose.tools import eq_
from ycmd.completers.cpp import clangd_completer
from ycmd import handlers
from mock import patch
from ycmd.tests.clangd import IsolatedYcmd

import os


def _TupleToLSPRange( tuple ):
  return { 'line': tuple[ 0 ], 'character': tuple[ 1 ] }


def _Check_Distance( point, start, end, expected ):
  point = _TupleToLSPRange( point )
  start = _TupleToLSPRange( start )
  end = _TupleToLSPRange( end )
  range = { 'start': start, 'end': end }
  result = clangd_completer.DistanceOfPointToRange( point, range )
  eq_( result, expected )


def ClangdCompleter_DistanceOfPointToRange_SingleLineRange_test():
  # Point to the left of range.
  _Check_Distance( ( 0, 0 ), ( 0, 2 ), ( 0, 5 ) , 2 )
  # Point inside range.
  _Check_Distance( ( 0, 4 ), ( 0, 2 ), ( 0, 5 ) , 0 )
  # Point to the right of range.
  _Check_Distance( ( 0, 8 ), ( 0, 2 ), ( 0, 5 ) , 3 )


def ClangdCompleter_DistanceOfPointToRange_MultiLineRange_test():
  # Point to the left of range.
  _Check_Distance( ( 0, 0 ), ( 0, 2 ), ( 3, 5 ) , 2 )
  # Point inside range.
  _Check_Distance( ( 1, 4 ), ( 0, 2 ), ( 3, 5 ) , 0 )
  # Point to the right of range.
  _Check_Distance( ( 3, 8 ), ( 0, 2 ), ( 3, 5 ) , 3 )


def ClangdCompleter_GetClangdCommand_test():
  TEST_PATH = '/test'
  EXPECTED = [ os.path.join( TEST_PATH, 'clangd' ) ]
  old_path = os.environ[ 'PATH' ]
  os.environ[ 'PATH' ] = TEST_PATH
  user_options = { 'clangd_uses_ycmd_caching': False }
  with patch( 'os.path.isfile', return_value=True ) as os_path_isfile:
    with patch( 'os.access', return_value=True ) as os_access:
      with patch( 'ycmd.completers.cpp.clangd_completer.GetVersion',
                  return_value = None ):
        eq_( clangd_completer.GetClangdCommand( user_options ), EXPECTED )
        os_path_isfile.assert_called()
        os_access.assert_called()
        # Clear cache.
        del user_options[ 'clangd_command' ]

        ARGS = [ 'a', 'b' ]
        user_options[ 'clangd_args' ] = ARGS
        EXPECTED.extend( ARGS )
        eq_( clangd_completer.GetClangdCommand( user_options ), EXPECTED )
        os_path_isfile.assert_called()
        os_access.assert_called()

        # Check caching works.
        del user_options[ 'clangd_args' ]
        eq_( clangd_completer.GetClangdCommand( user_options ), EXPECTED )
  os.environ[ 'PATH' ] = old_path

  with patch( 'os.path.isfile', return_value=False ) as os_path_isfile:
    eq_( clangd_completer.GetClangdCommand( {} ), None )
    os_path_isfile.assert_called()


def ClangdCompleter_ShouldEnableClangdCompleter_test():
  user_options = {}

  user_options[ 'use_clangd' ] = False
  eq_( clangd_completer.ShouldEnableClangdCompleter( user_options ), False )

  user_options = { 'use_clangd': True }
  # Finds the one in third_party
  eq_( clangd_completer.ShouldEnableClangdCompleter( user_options ), True )

  user_options = { 'use_clangd': True }
  with patch(
      'ycmd.completers.cpp.clangd_completer.GetClangdCommand',
      return_value = None ) as find_clangd_binary:
    eq_( clangd_completer.ShouldEnableClangdCompleter( user_options ), False )
    find_clangd_binary.assert_called()


class MockPopen:
  stdin = None
  stdout = None
  pid = 0

  def communicate( self ):
    return ( bytes(), None )


@patch( 'subprocess.Popen', return_value = MockPopen() )
def ClangdCompleter_GetVersion_test( mock_popen ):
  eq_( clangd_completer.GetVersion( '' ), None )
  mock_popen.assert_called()


@IsolatedYcmd()
def ClangdCompleter_ShutdownFail_test( app ):
  completer = handlers._server_state.GetFiletypeCompleter( [ 'cpp' ] )
  with patch.object( completer, 'ShutdownServer',
                     side_effect = Exception ) as shutdown_server:
    completer._server_handle = MockPopen()
    with patch.object( completer, 'ServerIsHealthy', return_value = True ):
      completer.Shutdown()
      shutdown_server.assert_called()
