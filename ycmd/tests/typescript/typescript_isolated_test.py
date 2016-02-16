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
from hamcrest import contains_inanyorder, has_entries
from .typescript_handlers_test import Typescript_Handlers_test
from mock import patch
import bottle


class TypeScript_Persistent_test( Typescript_Handlers_test ):

  @classmethod
  def setUpClass( cls ):
    bottle.debug( True )
    handlers.SetServerStateToDefaults()
    cls._app = TestApp( handlers.app )


  @patch( 'ycmd.completers.typescript.typescript_completer.MAX_DETAILED_COMPLETIONS', 2 )
  def Completion_MaxDetailedCompletion_test( self ):
    self._RunCompletionTest( {
      'expect': {
        'data': has_entries( {
          'completions': contains_inanyorder(
            self.CompletionEntryMatcher( 'methodA' ),
            self.CompletionEntryMatcher( 'methodB' ),
            self.CompletionEntryMatcher( 'methodC' )
          )
        } )
      }
    } )
