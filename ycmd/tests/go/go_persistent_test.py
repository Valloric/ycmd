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

from webtest import TestApp
from ycmd import handlers
from nose.tools import eq_
from hamcrest import assert_that, has_item
from .go_handlers_test import Go_Handlers_test
from ycmd.utils import ReadFile
import bottle


class Go_Persistent_test( Go_Handlers_test ):

  @classmethod
  def setUpClass( cls ):
    bottle.debug( True )
    handlers.SetServerStateToDefaults()
    cls._app = TestApp( handlers.app )


  @classmethod
  def tearDownClass( cls ):
    cls()._StopGoCodeServer()


  def Completion_Basic_test( self ):
    filepath = self._PathToTestFile( 'test.go' )
    completion_data = self._BuildRequest( filepath = filepath,
                                          filetype = 'go',
                                          contents = ReadFile( filepath ),
                                          force_semantic = True,
                                          line_num = 9,
                                          column_num = 11 )

    results = self._app.post_json( '/completions',
                                   completion_data ).json[ 'completions' ]
    assert_that( results,
                 has_item( self._CompletionEntryMatcher( u'Logger' ) ) )


  def _RunSubcommandGoTo( self, params ):
    filepath = self._PathToTestFile( 'goto.go' )
    contents = ReadFile( filepath )

    command = params[ 'command' ]
    goto_data = self._BuildRequest( completer_target = 'filetype_default',
                                    command_arguments = [ command ],
                                    line_num = 8,
                                    column_num = 8,
                                    contents = contents,
                                    filetype = 'go',
                                    filepath = filepath )

    results = self._app.post_json( '/run_completer_command',
                                   goto_data )

    eq_( {
      'line_num': 3, 'column_num': 6, 'filepath': filepath
    }, results.json )

    filepath = self._PathToTestFile( 'win.go' )
    contents = ReadFile( filepath )

    command = params[ 'command' ]
    goto_data = self._BuildRequest( completer_target = 'filetype_default',
                                    command_arguments = [ command ],
                                    line_num = 4,
                                    column_num = 7,
                                    contents = contents,
                                    filetype = 'go',
                                    filepath = filepath )

    results = self._app.post_json( '/run_completer_command',
                                   goto_data )

    eq_( {
      'line_num': 2, 'column_num': 6, 'filepath': filepath
    }, results.json )


  def Subcommand_GoTo_all_test( self ):
    tests = [
      { 'command': 'GoTo' },
      { 'command': 'GoToDefinition' },
      { 'command': 'GoToDeclaration' }
    ]

    for test in tests:
      yield self._RunSubcommandGoTo, test
