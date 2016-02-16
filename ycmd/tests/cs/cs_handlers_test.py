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
from ycmd.utils import OnTravis
import time


class Cs_Handlers_test( Handlers_test ):

  _file = __file__
  _app = None


  def _StartOmniSharpServer( self, filepath ):
    self._app.post_json(
      '/run_completer_command',
      self._BuildRequest( completer_target = 'filetype_default',
                          command_arguments = [ "StartServer" ],
                          filepath = filepath,
                          filetype = 'cs' )
    )


  def _StopOmniSharpServer( self, filepath ):
    self._app.post_json(
      '/run_completer_command',
      self._BuildRequest( completer_target = 'filetype_default',
                          command_arguments = [ 'StopServer' ],
                          filepath = filepath,
                          filetype = 'cs' )
    )


  def _WaitUntilOmniSharpServerReady( self, filepath ):
    retries = 100
    success = False

    # If running on Travis CI, keep trying forever. Travis will kill the worker
    # after 10 mins if nothing happens.
    while retries > 0 or OnTravis():
      result = self._app.get( '/ready', { 'subserver': 'cs' } ).json
      if result:
        success = True
        break
      request = self._BuildRequest( completer_target = 'filetype_default',
                                    command_arguments = [ 'ServerIsRunning' ],
                                    filepath = filepath,
                                    filetype = 'cs' )
      result = self._app.post_json( '/run_completer_command', request ).json
      if not result:
        raise RuntimeError( "OmniSharp failed during startup." )
      time.sleep( 0.2 )
      retries = retries - 1

    if not success:
      raise RuntimeError( "Timeout waiting for OmniSharpServer" )
