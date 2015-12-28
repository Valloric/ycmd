#!/usr/bin/env python
#
# Copyright (C) 2015 ycmd contributors.
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

from nose.tools import eq_
from hamcrest import assert_that, has_entry
from ...responses import NoDiagnosticSupport
from python_handlers_test import Python_Handlers_test
import httplib


class Python_Diagnostics_test( Python_Handlers_test ):

  # XXX(vheon): this is another instance where a mock Completer would be useful
  # jedi has a branch with linter functionality that we might think of adding
  # and then this test would change. With a mock Completer we would not have
  # test fragility
  def DoesntWork_test( self ):
    diag_data = self._BuildRequest( contents = "foo = 5",
                                    line_num = 2,
                                    filetype = 'python' )

    response = self._app.post_json( '/detailed_diagnostic',
                                    diag_data,
                                    expect_errors = True )

    eq_( response.status_code, httplib.INTERNAL_SERVER_ERROR )
    assert_that( response.json,
                 has_entry( 'exception',
                            has_entry( 'TYPE',
                                       NoDiagnosticSupport.__name__ ) ) )
