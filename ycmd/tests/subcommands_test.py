#!/usr/bin/env python
#
# Copyright (C) 2013 Google Inc.
#               2015 ycmd contributors
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
from .handlers_test import Handlers_test
try:
  from unittest import SkipTest
except ImportError:
  from unittest2 import SkipTest

class Subcommands_test( Handlers_test ):

  # XXX(vheon): The logic for this is actually in the `Completer` class.
  # Should we test this in a different way?
  # Maybe with a made up test object Completer.
  def Basic_test( self ):
    raise SkipTest

    subcommands_data = self._BuildRequest( completer_target = 'python' )

    eq_( [ 'GetDoc',
           'GoTo',
           'GoToDeclaration',
           'GoToDefinition',
           'RestartServer' ],
         self._app.post_json( '/defined_subcommands', subcommands_data ).json )


  def NoExplicitCompleterTargetSpecified_test( self ):
    raise SkipTest

    subcommands_data = self._BuildRequest( filetype = 'python' )

    eq_( [ 'GetDoc',
           'GoTo',
           'GoToDeclaration',
           'GoToDefinition',
           'RestartServer' ],
         self._app.post_json( '/defined_subcommands', subcommands_data ).json )
