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

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from hamcrest import ( assert_that, contains, contains_inanyorder, empty,
                       has_entry, has_entries, instance_of )
from nose.tools import eq_

from pprint import pformat
import requests

from ycmd.tests.java import ( PathToTestFile, SharedYcmd )
from ycmd.tests.test_utils import ( BuildRequest,
                                    CompletionEntryMatcher )
from ycmd.utils import ReadFile


@SharedYcmd
def DebugInfo_test( app ):
  request_data = BuildRequest( filetype = 'java' )
  assert_that(
    app.post_json( '/debug_info', request_data ).json,
    has_entry( 'completer', has_entries( {
      'name': 'Java',
      'servers': contains( has_entries( {
        'name': 'Java Language Server',
        'is_running': instance_of( bool ),
        'executable': instance_of( str ),
        'pid': instance_of( int ),
        'logfiles': contains( instance_of( str ),
                              instance_of( str ) )
      } ) )
    } ) )
  )
