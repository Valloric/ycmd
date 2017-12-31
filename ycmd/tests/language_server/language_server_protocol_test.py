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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from ycmd.completers.language_server import language_server_protocol as lsp
from hamcrest import assert_that, equal_to, calling, is_not, raises
from ycmd.tests.test_utils import UnixOnly, WindowsOnly


def ServerFileStateStore_RetrieveDelete_test():
  store = lsp.ServerFileStateStore()

  # New state object created
  file1_state = store[ 'file1' ]
  assert_that( file1_state.version, equal_to( 0 ) )
  assert_that( file1_state.checksum, equal_to( None ) )
  assert_that( file1_state.state, equal_to( lsp.ServerFileState.CLOSED ) )

  # Retrieve again unchanged
  file1_state = store[ 'file1' ]
  assert_that( file1_state.version, equal_to( 0 ) )
  assert_that( file1_state.checksum, equal_to( None ) )
  assert_that( file1_state.state, equal_to( lsp.ServerFileState.CLOSED ) )

  # Retrieve/create another one (we don't actually open this one)
  file2_state = store[ 'file2' ]
  assert_that( file2_state.version, equal_to( 0 ) )
  assert_that( file2_state.checksum, equal_to( None ) )
  assert_that( file2_state.state, equal_to( lsp.ServerFileState.CLOSED ) )

  # Checking the next action progresses the state
  assert_that( file1_state.GetFileUpdateAction( 'test contents' ),
               equal_to( lsp.ServerFileState.OPEN_FILE ) )
  assert_that( file1_state.version, equal_to( 1 ) )
  assert_that( file1_state.checksum, is_not( equal_to( None ) ) )
  assert_that( file1_state.state, equal_to( lsp.ServerFileState.OPEN ) )

  # Replacing the same file is no-op
  assert_that( file1_state.GetFileUpdateAction( 'test contents' ),
               equal_to( lsp.ServerFileState.NO_ACTION ) )
  assert_that( file1_state.version, equal_to( 1 ) )
  assert_that( file1_state.checksum, is_not( equal_to( None ) ) )
  assert_that( file1_state.state, equal_to( lsp.ServerFileState.OPEN ) )

  # Replacing the same file is no-op
  assert_that( file1_state.GetFileUpdateAction( 'test contents changed' ),
               equal_to( lsp.ServerFileState.CHANGE_FILE ) )
  assert_that( file1_state.version, equal_to( 2 ) )
  assert_that( file1_state.checksum, is_not( equal_to( None ) ) )
  assert_that( file1_state.state, equal_to( lsp.ServerFileState.OPEN ) )

  # Closing an open file progressed the state
  assert_that( file1_state.GetFileCloseAction(),
               equal_to( lsp.ServerFileState.CLOSE_FILE ) )
  assert_that( file1_state.version, equal_to( 2 ) )
  assert_that( file1_state.checksum, is_not( equal_to( None ) ) )
  assert_that( file1_state.state, equal_to( lsp.ServerFileState.CLOSED ) )

  # Closing a closed file is a noop
  assert_that( file2_state.GetFileCloseAction(),
               equal_to( lsp.ServerFileState.NO_ACTION ) )
  assert_that( file2_state.version, equal_to( 0 ) )
  assert_that( file2_state.checksum, equal_to( None ) )
  assert_that( file2_state.state, equal_to( lsp.ServerFileState.CLOSED ) )


@UnixOnly
def UriToFilePath_Unix_test():
  assert_that( calling( lsp.UriToFilePath ).with_args( 'test' ),
               raises( lsp.InvalidUriException ) )

  assert_that( lsp.UriToFilePath( 'file:/usr/local/test/test.test' ),
               equal_to( '/usr/local/test/test.test' ) )
  assert_that( lsp.UriToFilePath( 'file:///usr/local/test/test.test' ),
               equal_to( '/usr/local/test/test.test' ) )


@WindowsOnly
def UriToFilePath_Windows_test():
  assert_that( calling( lsp.UriToFilePath ).with_args( 'test' ),
               raises( lsp.InvalidUriException ) )

  assert_that( lsp.UriToFilePath( 'file:c:/usr/local/test/test.test' ),
               equal_to( 'C:\\usr\\local\\test\\test.test' ) )
  assert_that( lsp.UriToFilePath( 'file://c:/usr/local/test/test.test' ),
               equal_to( 'C:\\usr\\local\\test\\test.test' ) )


@UnixOnly
def FilePathToUri_Unix_test():
  assert_that( lsp.FilePathToUri( '/usr/local/test/test.test' ),
               equal_to( 'file:///usr/local/test/test.test' ) )


@WindowsOnly
def FilePathToUri_Windows_test():
  assert_that( lsp.FilePathToUri( 'C:\\usr\\local\\test\\test.test' ),
               equal_to( 'file://C:/usr/local/test/test.test' ) )
