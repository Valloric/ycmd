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

from hamcrest import assert_that, has_entry, contains_string
from .rust_handlers_test import Rust_Handlers_test
from ycmd.utils import ReadFile


class Rust_Isolated_test( Rust_Handlers_test ):

  def setUp( self ):
    self._SetUpApp()
    self._WaitUntilRacerdServerReady()


  def tearDown( self ):
    self._StopRacerdServer()


  def Completion_WhenStandardLibraryCompletionFails_MentionRustSrcPath_test( self ):
    filepath = self._PathToTestFile( 'std_completions.rs' )
    contents = ReadFile( filepath )

    completion_data = self._BuildRequest( filepath = filepath,
                                          filetype = 'rust',
                                          contents = contents,
                                          force_semantic = True,
                                          line_num = 5,
                                          column_num = 11 )

    response = self._app.post_json( '/completions',
                                    completion_data,
                                    expect_errors = True ).json
    assert_that( response,
                 has_entry( 'message',
                            contains_string( 'rust_src_path' ) ) )
