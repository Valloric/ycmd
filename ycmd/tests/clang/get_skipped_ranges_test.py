# Copyright (C) 2016 Davit Samvelyan
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
from hamcrest import ( assert_that, contains )

from ycmd.tests.clang import PathToTestFile, SharedYcmd
from ycmd.tests.test_utils import BuildRequest
from ycmd.responses import ( BuildRangeData, Range, Location )
from ycmd.utils import ReadFile
import http.client


_TEST_FILE = PathToTestFile( 'GetSkippedRanges_Clang_test.cc' )


@SharedYcmd
def setUpModule( app ):
  app.post_json( '/load_extra_conf_file', {
    'filepath': PathToTestFile( '.ycm_extra_conf.py' ) } )
  request = {
    'filetype': 'cpp',
    'filepath': _TEST_FILE,
    'event_name': 'FileReadyToParse',
    'contents': ReadFile( _TEST_FILE )
  }
  app.post_json( '/event_notification', BuildRequest( **request ),
                 expect_errors = False )


def _BuildRangeData( sl, sc, el, ec ):
  return BuildRangeData( Range( Location( sl, sc, _TEST_FILE ),
                                Location( el, ec, _TEST_FILE ) ) )


@SharedYcmd
def _RunTest( app, expect ):
  request = {
    'filetypes': 'cpp',
    'filepath': _TEST_FILE,
  }
  response = app.post_json( '/skipped_ranges', BuildRequest( **request ),
                            expect_errors = False )

  eq_( response.status_code, http.client.OK )
  assert_that( response.json, expect )


@SharedYcmd
def SkippedRanges_test( app ):
  _RunTest( contains(
              _BuildRangeData( 2, 2, 4, 7 ),
              _BuildRangeData( 11, 2, 13, 7 ),
            ) )
