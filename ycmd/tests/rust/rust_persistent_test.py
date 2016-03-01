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

from nose.tools import eq_
from hamcrest import assert_that, has_items
from .rust_handlers_test import Rust_Handlers_test
from ycmd.utils import ReadFile


class Rust_Persistent_test( Rust_Handlers_test ):

  @classmethod
  def setUpClass( cls ):
    cls._SetUpApp()
    cls()._WaitUntilRacerdServerReady()


  @classmethod
  def tearDownClass( cls ):
    cls()._StopRacerdServer()


  def Completion_Basic_test( self ):
    filepath = self._PathToTestFile( 'test.rs' )
    contents = ReadFile( filepath )

    completion_data = self._BuildRequest( filepath = filepath,
                                          filetype = 'rust',
                                          contents = contents,
                                          force_semantic = True,
                                          line_num = 9,
                                          column_num = 11 )

    results = self._app.post_json( '/completions',
                                   completion_data ).json[ 'completions' ]

    assert_that( results,
                 has_items( self._CompletionEntryMatcher( 'build_rocket' ),
                            self._CompletionEntryMatcher( 'build_shuttle' ) ) )


  def _RunSubcommandGoTo( self, params ):
    filepath = self._PathToTestFile( 'test.rs' )
    contents = ReadFile( filepath )

    command = params[ 'command' ]
    goto_data = self._BuildRequest( completer_target = 'filetype_default',
                                    command_arguments = [ command ],
                                    line_num = 7,
                                    column_num = 12,
                                    contents = contents,
                                    filetype = 'rust',
                                    filepath = filepath )

    results = self._app.post_json( '/run_completer_command',
                                   goto_data )

    eq_( {
      'line_num': 1, 'column_num': 8, 'filepath': filepath
    }, results.json )


  def Subcommand_GoTo_all_test( self ):
    tests = [
      { 'command': 'GoTo' },
      { 'command': 'GoToDefinition' },
      { 'command': 'GoToDeclaration' }
    ]

    for test in tests:
      yield self._RunSubcommandGoTo, test
