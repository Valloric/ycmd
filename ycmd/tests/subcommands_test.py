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
from ycmd.completers.completer import Completer


class DummyCompleter( Completer ):
  def __init__( self, user_options ):
    pass


  def SupportedFiletypes( self ):
    return [ 'dummy_filetype' ]


  def GetSubcommandsMap( self ):
    return {
      'A': lambda x: x,
      'B': lambda x: x,
      'C': lambda x: x
    }


class Subcommands_test( Handlers_test ):

  def Basic_test( self, *args ):
    self.InstallCompleter( DummyCompleter, 'dummy_filetype' )
    subcommands_data = self._BuildRequest( completer_target = 'dummy_filetype' )

    eq_( [ 'A', 'B', 'C' ],
         self._app.post_json( '/defined_subcommands', subcommands_data ).json )


  def NoExplicitCompleterTargetSpecified_test( self ):
    self.InstallCompleter( DummyCompleter, 'dummy_filetype' )
    subcommands_data = self._BuildRequest( filetype = 'dummy_filetype' )

    eq_( [ 'A', 'B', 'C' ],
         self._app.post_json( '/defined_subcommands', subcommands_data ).json )
