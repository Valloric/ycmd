# Copyright (C) 2015 ycmd contributors
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

from ..handlers_test import Handlers_test
from hamcrest import assert_that
from ycmd.utils import ReadFile


class Typescript_Handlers_test( Handlers_test ):

  _file = __file__
  _app = None


  def CompletionEntryMatcher( self, insertion_text, menu_text = None ):
    if not menu_text:
      menu_text = insertion_text

    extra_params = { 'menu_text': menu_text }
    return self._CompletionEntryMatcher( insertion_text,
                                         extra_params = extra_params )


  def _RunCompletionTest( self, test ):
    filepath = self._PathToTestFile( 'test.ts' )
    contents = ReadFile( filepath )

    event_data = self._BuildRequest( filepath = filepath,
                                     filetype = 'typescript',
                                     contents = contents,
                                     event_name = 'BufferVisit' )

    self._app.post_json( '/event_notification', event_data )

    completion_data = self._BuildRequest( filepath = filepath,
                                          filetype = 'typescript',
                                          contents = contents,
                                          force_semantic = True,
                                          line_num = 12,
                                          column_num = 6 )

    response = self._app.post_json( '/completions', completion_data )
    assert_that( response.json, test[ 'expect' ][ 'data' ] )
