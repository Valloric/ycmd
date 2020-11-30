# Copyright (C) 2020 ycmd contributors
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

from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
from socketserver import ThreadingMixIn
import select
import sys


class StoppableWSGIServer( ThreadingMixIn, WSGIServer ):
  shutdown_requested = False
  daemon_threads = True

  def __init__( self, app, host, port, threads ):
    super().__init__( ( host, port ), WSGIRequestHandler )
    self.set_app( app )


  def Run( self ):
    """Wrapper of TcpWSGIServer run method. It prevents a traceback from
    asyncore."""

    # Message for compatibility with clients who expect the output from
    # waitress.serve here
    if sys.stdin is not None:
      print( f'serving on http://{ self.server_name }:{ self.server_port }' )

    try:
      self.serve_forever()
    except select.error:
      if not self.shutdown_requested:
        raise


  def Shutdown( self ):
    """Properly shutdown the server."""
    self.shutdown_requested = True
    self.server_close()
    self.shutdown()
