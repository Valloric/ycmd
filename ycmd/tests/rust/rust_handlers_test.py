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

from ..handlers_test import Handlers_test

class Rust_Handlers_test( Handlers_test ):

  def __init__( self ):
    self._file = __file__


  def tearDown( self ):
    self._StopServer()


  def _StopServer( self ):
    try:
      self._app.post_json(
        '/run_completer_command',
        self._BuildRequest( command_arguments = [ 'StopServer' ],
                            filetype = 'rust',
                            completer_target = 'filetype_default' )
      )
    except:
      pass

